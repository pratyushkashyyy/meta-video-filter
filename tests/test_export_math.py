from pathlib import Path

from meta_video_filter.export import build_crop_filter, build_export_command, choose_crop_box, resolve_video_encoder
from meta_video_filter.config import ASPECT_RATIOS


def test_choose_crop_box_landscape_to_vertical_centers_subject():
    crop = choose_crop_box(1920, 1080, 1080, 1920, subject_center=(1400, 540))
    assert crop.width == 608
    assert crop.height == 1080
    assert crop.x > 1000
    assert crop.y == 0


def test_choose_crop_box_portrait_to_square():
    crop = choose_crop_box(1080, 1920, 1080, 1080)
    assert crop.width == 1080
    assert crop.height == 1080
    assert crop.x == 0
    assert crop.y == 420


def test_build_crop_filter():
    crop = choose_crop_box(1920, 1080, 1080, 1080)
    assert build_crop_filter(crop, ASPECT_RATIOS["1:1"]) == "crop=1080:1080:420:0,scale=1080:1080:flags=lanczos"


def test_build_export_command_uses_nvenc_quality_flags():
    command = build_export_command(
        "ffmpeg",
        Path("input.mp4"),
        Path("output.mp4"),
        "crop=1080:1080:420:0,scale=1080:1080:flags=lanczos",
        "h264_nvenc",
    )
    assert "h264_nvenc" in command
    assert "-cq" in command
    assert "-crf" not in command


def test_resolve_video_encoder_cpu_request():
    assert resolve_video_encoder("ffmpeg", requested="cpu") == "libx264"
