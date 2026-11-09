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