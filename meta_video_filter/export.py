from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from .config import ASPECT_RATIOS, AspectRatioPreset
from .dependencies import find_bundled_or_path_executable

if TYPE_CHECKING:
    from .scoring import PersonDetector

LogCallback = Callable[[str], None]
CancelCallback = Callable[[], bool]


@dataclass(frozen=True)
class CropBox:
    x: int
    y: int
    width: int
    height: int


def require_ffmpeg() -> str:
    ffmpeg = find_bundled_or_path_executable("ffmpeg", "ffmpeg.exe")
    if not ffmpeg:
        raise RuntimeError("ffmpeg was not found on PATH. Install ffmpeg before exporting videos.")
    return ffmpeg


def ffmpeg_has_encoder(ffmpeg: str, encoder: str) -> bool:
    try:
        completed = subprocess.run(
            [ffmpeg, "-hide_banner", "-encoders"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        return False
    return encoder in completed.stdout or encoder in completed.stderr


def cuda_is_available() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def resolve_video_encoder(ffmpeg: str, requested: str = "auto") -> str:
    """Choose the FFmpeg video encoder for exports."""
    import os

    env_encoder = os.getenv("META_VIDEO_FILTER_VIDEO_ENCODER")
    if requested == "auto" and env_encoder:
        requested = env_encoder

    if requested == "cpu":
        return "libx264"
    if requested in {"h264_nvenc", "libx264"}:
        return requested
    if requested != "auto":
        return requested

    if cuda_is_available() and ffmpeg_has_encoder(ffmpeg, "h264_nvenc"):
        return "h264_nvenc"
    return "libx264"


def choose_crop_box(
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
    subject_center: tuple[float, float] | None = None,
) -> CropBox:
    if source_width <= 0 or source_height <= 0:
        raise ValueError("Source dimensions must be positive.")
    if target_width <= 0 or target_height <= 0:
        raise ValueError("Target dimensions must be positive.")

    target_ratio = target_width / target_height
    source_ratio = source_width / source_height

    if source_ratio > target_ratio:
        crop_height = source_height
        crop_width = int(round(source_height * target_ratio))
    else:
        crop_width = source_width
        crop_height = int(round(source_width / target_ratio))

    crop_width = max(2, min(source_width, crop_width))
    crop_height = max(2, min(source_height, crop_height))
    crop_width -= crop_width % 2
    crop_height -= crop_height % 2

    center_x = subject_center[0] if subject_center else source_width / 2
    center_y = subject_center[1] if subject_center else source_height / 2

    x = int(round(center_x - crop_width / 2))
    y = int(round(center_y - crop_height / 2))
    x = max(0, min(source_width - crop_width, x))
    y = max(0, min(source_height - crop_height, y))
    x -= x % 2
    y -= y % 2

    return CropBox(x=x, y=y, width=crop_width, height=crop_height)


def get_video_dimensions(video_path: str | Path) -> tuple[int, int]:
    import cv2

    cap = cv2.VideoCapture(str(video_path))
    try:
        if not cap.isOpened():
            raise RuntimeError(f"Could not open {Path(video_path).name}")
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width <= 0 or height <= 0:
            raise RuntimeError(f"Could not read dimensions for {Path(video_path).name}")
        return width, height
    finally:
        cap.release()


def estimate_subject_center(
    video_path: str | Path,
    detector: "PersonDetector",
    samples: int = 12,
    should_cancel: CancelCallback | None = None,
) -> tuple[float, float] | None:
    import cv2

    cap = cv2.VideoCapture(str(video_path))
    try:
        if not cap.isOpened():
            return None

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count <= 0:
            return None

        weighted_x = 0.0
        weighted_y = 0.0
        total_weight = 0.0

        for i in range(samples):
            if should_cancel and should_cancel():
                return None
            frame_index = int((i + 0.5) * frame_count / samples)
            cap.set(cv2.CAP_PROP_POS_FRAMES, min(frame_count - 1, frame_index))
            ret, frame = cap.read()
            if not ret:
                continue

            for x1, y1, x2, y2, confidence in detector.detect_person_boxes(frame):
                area = max(1.0, (x2 - x1) * (y2 - y1))
                weight = area * max(0.1, confidence)
                weighted_x += ((x1 + x2) / 2) * weight
                weighted_y += ((y1 + y2) / 2) * weight
                total_weight += weight

        if total_weight <= 0:
            return None
        return weighted_x / total_weight, weighted_y / total_weight
    finally:
        cap.release()


def build_crop_filter(crop: CropBox, preset: AspectRatioPreset) -> str:
    return (
        f"crop={crop.width}:{crop.height}:{crop.x}:{crop.y},"
        f"scale={preset.width}:{preset.height}:flags=lanczos"
    )


def build_export_command(
    ffmpeg: str,
    input_path: Path,
    output_path: Path,
    video_filter: str,
    video_encoder: str,
) -> list[str]:
    command = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-vf",
        video_filter,
        "-c:v",
        video_encoder,
    ]

    if video_encoder == "h264_nvenc":
        command.extend(["-cq", "23", "-preset", "p4"])
    else:
        command.extend(["-crf", "23", "-preset", "medium"])

    command.extend(
        [
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )
    return command


def export_video(
    input_path: str | Path,
    output_path: str | Path,
    ratio_key: str,
    detector: "PersonDetector",
    video_encoder: str = "auto",
    log: LogCallback | None = None,
    should_cancel: CancelCallback | None = None,
) -> None:
    if ratio_key not in ASPECT_RATIOS:
        raise ValueError(f"Unsupported ratio: {ratio_key}")

    ffmpeg = require_ffmpeg()
    input_path = Path(input_path)
    output_path = Path(output_path)
    preset = ASPECT_RATIOS[ratio_key]
    source_width, source_height = get_video_dimensions(input_path)
    subject_center = estimate_subject_center(input_path, detector, should_cancel=should_cancel)
    crop = choose_crop_box(source_width, source_height, preset.width, preset.height, subject_center)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    video_filter = build_crop_filter(crop, preset)
    resolved_encoder = resolve_video_encoder(ffmpeg, requested=video_encoder)

    if should_cancel and should_cancel():
        return

    if log:
        log(f"Exporting {input_path.name} as {ratio_key} with {resolved_encoder} -> {output_path}")

    command = build_export_command(ffmpeg, input_path, output_path, video_filter, resolved_encoder)
    completed = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if completed.returncode == 0:
        return

    if resolved_encoder != "libx264":
        if log:
            log(f"GPU export failed for {input_path.name}; retrying with CPU encoder libx264.")
        fallback_command = build_export_command(ffmpeg, input_path, output_path, video_filter, "libx264")
        subprocess.run(fallback_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return

    completed.check_returncode()
