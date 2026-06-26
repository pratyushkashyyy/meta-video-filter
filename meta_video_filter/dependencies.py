from __future__ import annotations

import shutil
import sys
from pathlib import Path

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None


def find_bundled_or_path_executable(*names: str) -> str | None:
    """Find a command on PATH or beside the frozen/source executable."""
    search_dirs: list[Path] = []

    if getattr(sys, "frozen", False):
        search_dirs.append(Path(sys.executable).resolve().parent)

    for directory in search_dirs:
        for name in names:
            candidate = directory / name
            if candidate.exists():
                return str(candidate)

    for name in names:
        path = shutil.which(name)
        if path:
            return path

    # imageio-ffmpeg ships a platform-specific FFmpeg executable. Keeping this
    # as a final fallback makes the frozen app self-contained on every desktop OS.
    if imageio_ffmpeg is not None:
        try:
            executable = Path(imageio_ffmpeg.get_ffmpeg_exe())
            if executable.exists():
                return str(executable)
        except (OSError, RuntimeError):
            pass

    return None
