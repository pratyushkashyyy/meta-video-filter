#!/usr/bin/env python3
"""Download the pinned YOLO model used by release builds."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from urllib.request import Request, urlopen


MODEL_URL = "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt"
MIN_MODEL_SIZE = 1_000_000


def ensure_model(output_path: Path) -> Path:
    output_path = output_path.expanduser().resolve()
    if output_path.exists() and output_path.stat().st_size >= MIN_MODEL_SIZE:
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(f"{output_path.suffix}.part")
    temporary_path.unlink(missing_ok=True)
    request = Request(MODEL_URL, headers={"User-Agent": "MetaVideoFilter/0.1"})

    try:
        with urlopen(request, timeout=60) as response, temporary_path.open("wb") as file:
            while chunk := response.read(1024 * 1024):
                file.write(chunk)
    except OSError as exc:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(f"Could not download the YOLO model: {exc}") from exc

    if temporary_path.stat().st_size < MIN_MODEL_SIZE:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError("The downloaded YOLO model is incomplete.")

    os.replace(temporary_path, output_path)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare the bundled YOLO model for a release build.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/release-assets/yolov8n.pt"),
        help="Location for the downloaded yolov8n.pt file.",
    )
    args = parser.parse_args()
    print(ensure_model(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
