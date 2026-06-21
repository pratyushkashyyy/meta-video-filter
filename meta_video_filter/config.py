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
    "1:1": AspectRatioPreset("1:1", "1:1 Square Feed", 1080, 1080),
    "4:5": AspectRatioPreset("4:5", "4:5 Vertical Feed", 1080, 1350),
}

DEFAULT_RATIOS = ("9:16", "1:1", "4:5")
