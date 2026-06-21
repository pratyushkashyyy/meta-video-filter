from __future__ import annotations

import argparse
import threading
from pathlib import Path

from meta_video_filter.config import DEFAULT_RATIOS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score videos and export Meta ad aspect ratios.")
    parser.add_argument("input_folder", help="Folder containing input videos.")
    parser.add_argument(
        "--ratios",
        nargs="+",
        default=list(DEFAULT_RATIOS),
        choices=["9:16", "1:1", "4:5"],
        help="Aspect ratios to export for Group A/B videos.",
    )
    parser.add_argument(
        "--yolo-device",
        default="auto",
        choices=["auto", "cpu", "cuda:0"],
        help="Device for YOLO person detection.",
    )
    parser.add_argument(
        "--video-encoder",
        default="auto",
        choices=["auto", "cpu", "h264_nvenc", "libx264"],
        help="Encoder for aspect-ratio exports.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cancel_event = threading.Event()

    try:
        from meta_video_filter.pipeline import ProcessingCancelled, run_pipeline

        run_pipeline(
            Path(args.input_folder),
            Path(args.input_folder) / "Meta_Ad_Output",
            args.ratios,
            yolo_device=args.yolo_device,
            video_encoder=args.video_encoder,
            log=print,
            progress=lambda done, total: print(f"Progress: {done}/{total}"),
            cancel_event=cancel_event,
        )
    except KeyboardInterrupt:
        cancel_event.set()
        print("Cancelled.")
        return 130
    except Exception as exc:
        if exc.__class__.__name__ == "ProcessingCancelled":
            print("Cancelled.")
            return 130
        print(f"Failed: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
