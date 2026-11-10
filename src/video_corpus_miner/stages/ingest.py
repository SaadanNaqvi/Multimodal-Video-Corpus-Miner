import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path

from video_corpus_miner.schemas import VideoRecord

FFPROBE_TIMEOUT_S = 30
HASH_CHUNK_BYTES = 1024 * 1024  # 1 MB, so large videos don't fill memory


def read_manifest(manifest_path: Path) -> list[Path]:
    results: list[Path] = []
    manifest_dir = Path(manifest_path).parent

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_entries = data if isinstance(data, list) else data.get("files", [])

    for entry in raw_entries:
        raw_path = entry["path"] if isinstance(entry, dict) else entry
        video_path = Path(raw_path)

        if not video_path.is_absolute():
            video_path = (manifest_dir / video_path).resolve()

        results.append(video_path)

    return results


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def run_ffprobe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=FFPROBE_TIMEOUT_S,
    )
    return json.loads(result.stdout)


def _parse_frame_rate(rate: str | None) -> float | None:
    """Turn an ffprobe rate like "30000/1001" into a float.

    Returns None for missing or meaningless rates such as "0/0".
    """
    if not rate:
        return None
    try:
        value = Fraction(rate)
    except (ValueError, ZeroDivisionError):
        return None
    return float(value) if value > 0 else None


def parse_probe(probe: dict) -> dict:
    """Pull the fields we need out of ffprobe's JSON.

    Raises ValueError if there's no video stream or no usable duration,
    since later stages can't work without them.
    """
    streams = probe.get("streams", [])

    # The video stream isn't always first, so search by type.
    # Cover art is stored as a one-frame video stream, so skip it.
    video = next(
        (
            s for s in streams
            if s.get("codec_type") == "video"
            and not s.get("disposition", {}).get("attached_pic")
        ),
        None,
    )
    if video is None:
        raise ValueError("no video stream")

    raw_duration = probe.get("format", {}).get("duration") or video.get("duration")
    if raw_duration is None:
        raise ValueError("no duration")
    duration_s = float(raw_duration)
    if duration_s <= 0:
        raise ValueError(f"invalid duration: {raw_duration}")

    fps = _parse_frame_rate(video.get("avg_frame_rate")) or _parse_frame_rate(
        video.get("r_frame_rate")
    )

    return {
        "duration_s": duration_s,
        "fps": fps,
        "width": video.get("width"),
        "height": video.get("height"),
        "has_audio": any(s.get("codec_type") == "audio" for s in streams),
    }


def ingest_video(path: Path) -> VideoRecord:
    path_str = str(path)

    if not path.is_file():
        return VideoRecord(path=path_str, status="quarantined", error="file not found")

    try:
        content_hash = hash_file(path)
        metadata = parse_probe(run_ffprobe(path))
    except subprocess.CalledProcessError as e:
        message = re.sub(r" @ 0x[0-9a-f]+", "", (e.stderr or "").strip())
        message = message or f"ffprobe exited with code {e.returncode}"
        return VideoRecord(path=path_str, status="quarantined", error=f"ffprobe: {message}")
    except subprocess.TimeoutExpired:
        return VideoRecord(
            path=path_str,
            status="quarantined",
            error=f"ffprobe timed out after {FFPROBE_TIMEOUT_S}s",
        )
    except (OSError, ValueError, KeyError, TypeError) as e:
        return VideoRecord(path=path_str, status="quarantined", error=str(e))

    return VideoRecord(path=path_str, status="ok", content_hash=content_hash, **metadata)


def ingest(manifest_path: Path, output_path: Path) -> list[VideoRecord]:
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe not found; run this inside the Nix shell")

    records = [ingest_video(path) for path in read_manifest(manifest_path)]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(asdict(record)) + "\n")

    return records


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python -m video_corpus_miner.stages.ingest MANIFEST OUTPUT")

    results = ingest(Path(sys.argv[1]), Path(sys.argv[2]))
    ok = sum(r.status == "ok" for r in results)
    print(f"{ok} ok, {len(results) - ok} quarantined -> {sys.argv[2]}")
