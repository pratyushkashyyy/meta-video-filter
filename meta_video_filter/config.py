from __future__ import annotations

from dataclasses import dataclass

VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi", ".webm")


@dataclass(frozen=True)
class AspectRatioPreset:
    key: str
    label: str
    width: int
    height: int

    @property
    def folder_name(self) -> str:
        return self.key.replace(":", "x")


ASPECT_RATIOS = {
    "9:16": AspectRatioPreset("9:16", "9:16 Reels / Stories", 1080, 1920),
}

DEFAULT_RATIOS = ("9:16",)
