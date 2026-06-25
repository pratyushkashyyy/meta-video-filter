from __future__ import annotations

import argparse
import threading
from pathlib import Path

from meta_video_filter.config import DEFAULT_RATIOS
from meta_video_filter.distribution import (
    MAX_GROUP_COUNT,
    MAX_VIDEOS_PER_GROUP,
    MIN_GROUP_COUNT,
    MIN_VIDEOS_PER_GROUP,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score videos and export Meta ad aspect ratios.")
    parser.add_argument("input_folder", help="Folder containing input videos.")
    parser.add_argument(
        "--ratios",
        nargs="+",
        default=list(DEFAULT_RATIOS),
        choices=["9:16", "1:1", "4:5"],
        help="Aspect ratios to export for selected group videos.",
    )
    parser.add_argument(
        "--groups",
        type=int,
        default=2,
        choices=range(MIN_GROUP_COUNT, MAX_GROUP_COUNT + 1),
        metavar=f"{MIN_GROUP_COUNT}-{MAX_GROUP_COUNT}",
        help="Number of ranked output groups to create.",
    )
    parser.add_argument(
        "--videos-per-group",
        type=int,
        default=10,
        choices=range(MIN_VIDEOS_PER_GROUP, MAX_VIDEOS_PER_GROUP + 1),
        metavar=f"{MIN_VIDEOS_PER_GROUP}-{MAX_VIDEOS_PER_GROUP}",
        help="Maximum number of exported videos in each group.",
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
            group_count=args.groups,
            videos_per_group=args.videos_per_group,
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
