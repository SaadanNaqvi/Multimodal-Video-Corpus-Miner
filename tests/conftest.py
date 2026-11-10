import shutil
import subprocess
from pathlib import Path

import pytest


def _ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


@pytest.fixture(scope="session")
def fixtures_dir(tmp_path_factory) -> Path:
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not available; run inside the Nix shell")

    out = tmp_path_factory.mktemp("fixtures")
    video = ["-f", "lavfi", "-i", "testsrc=duration=1:size=64x64:rate=10"]
    audio = ["-f", "lavfi", "-i", "sine=frequency=440:duration=1"]

    _ffmpeg(*video, *audio, "-shortest", "-pix_fmt", "yuv420p", str(out / "valid.mp4"))
    _ffmpeg(*video, "-pix_fmt", "yuv420p", str(out / "no_audio.mp4"))
    (out / "corrupt.mp4").write_bytes(b"this is not a video" * 50)
    _ffmpeg(*audio, str(out / "audio_only.m4a"))

    return out
