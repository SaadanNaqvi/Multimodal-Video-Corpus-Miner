import json
import subprocess
from pathlib import Path
from schemas import VideoRecord

def read_manifest(manifest_path) -> list[Path]:
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

def hash_file(path: Path) -> str: ...
def run_ffprobe(path: Path) -> dict: ...
def parse_probe(probe: dict) -> dict: ...
def ingest_video(path: Path) -> VideoRecord: ...
def ingest(manifest_path: Path, output_path: Path) -> list[VideoRecord]: ...