from dataclasses import dataclass
from pathlib import Path

@dataclass
class VideoRecord:
    path: str
    status: str
    error: str | None = None
    content_hash: str | None = None
    duration_s: float | None = None
    fps: float | None = None
    width: int | None = None
    height: int | None = None
    has_audio: bool | None = None

def red_manifest(manifest_path: Path) -> list[Path]: ...
def hash_file(path: Path) -> str: ...
def run_ffprobe(path: Path) -> dict: ...
def parse_probe(probe: dict) -> dict: ...
def ingest_video(path: Path) -> VideoRecord: ...
def ingest(manifest_path: Path, output_path: Path) -> list[VideoRecord]: ...