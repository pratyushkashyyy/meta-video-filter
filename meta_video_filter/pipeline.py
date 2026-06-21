from __future__ import annotations

import csv
import shutil
import threading
from pathlib import Path
from typing import Callable, Iterable

from .config import ASPECT_RATIOS, VIDEO_EXTENSIONS
from .distribution import VideoRow, distribute_videos
from .export import export_video
from .scoring import PersonDetector, iter_video_files, save_thumbnail, score_video

LogCallback = Callable[[str], None]
ProgressCallback = Callable[[int, int], None]
ResultCallback = Callable[[dict], None]


class ProcessingCancelled(Exception):
    pass


def _cancelled(cancel_event: threading.Event | None) -> bool:
    return bool(cancel_event and cancel_event.is_set())


def _copy_group_videos(input_folder: Path, group_rows: list[VideoRow], group_folder: Path) -> None:
    group_folder.mkdir(parents=True, exist_ok=True)
    for row in group_rows:
        source = input_folder / str(row["file"])
        if source.exists():
            shutil.copy2(source, group_folder / str(row["file"]))


def _write_report(path: Path, rows: list[VideoRow]) -> None:
    preferred_fields = [
        "file",
        "final_score",
        "hook_motion",
        "motion_avg",
        "scene_cuts",
        "text_overlay_hits",
        "person_hits",
        "brightness",
        "sharpness",
        "audio_rms",
        "audio_spike",
        "static_intro_penalty",
        "group",
        "error",
    ]
    extra_fields = sorted({key for row in rows for key in row if key not in preferred_fields})
    fields = preferred_fields + extra_fields
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_pipeline(
    input_folder: str | Path,
    output_folder: str | Path,
    ratio_keys: Iterable[str],
    yolo_device: str = "auto",
    video_encoder: str = "auto",
    log: LogCallback | None = None,
    progress: ProgressCallback | None = None,
    result: ResultCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> list[VideoRow]:
    input_folder = Path(input_folder)
    output_folder = Path(output_folder)
    ratio_keys = tuple(ratio_keys)
    for ratio_key in ratio_keys:
        if ratio_key not in ASPECT_RATIOS:
            raise ValueError(f"Unsupported ratio: {ratio_key}")

    if not input_folder.exists():
        raise FileNotFoundError(f"Input folder does not exist: {input_folder}")

    output_folder.mkdir(parents=True, exist_ok=True)
    thumbnail_folder = output_folder / "thumbnails"
    thumbnail_folder.mkdir(parents=True, exist_ok=True)

    detector = PersonDetector(device=yolo_device)
    files = iter_video_files(input_folder, VIDEO_EXTENSIONS)
    if not files:
        raise RuntimeError("No videos found in the selected input folder.")

    if log:
        log(f"Scanning {len(files)} videos")
        log(f"YOLO device: {detector.resolved_device}")
        log(f"Video export encoder request: {video_encoder}")

    rows: list[VideoRow] = []
    total_steps = len(files)
    done_steps = 0

    for video_path in files:
        if _cancelled(cancel_event):
            raise ProcessingCancelled()

        if log:
            log(f"Scoring {video_path.name}")
        try:
            scored = score_video(
                video_path,
                detector=detector,
                log=log,
                should_cancel=lambda: _cancelled(cancel_event),
            )
            if scored is None:
                row = {"file": video_path.name, "error": "Could not score video", "group": ""}
            else:
                row = scored.to_dict()
                save_thumbnail(video_path, thumbnail_folder / f"{video_path.stem}.jpg")
        except Exception as exc:
            row = {"file": video_path.name, "error": str(exc), "group": ""}
            if log:
                log(f"Failed {video_path.name}: {exc}")

        rows.append(row)
        done_steps += 1
        if progress:
            progress(done_steps, total_steps)

    scored_rows = [row for row in rows if not row.get("error")]
    error_rows = [row for row in rows if row.get("error")]
    if not scored_rows:
        raise RuntimeError("No videos could be scored.")

    group_a, group_b, later = distribute_videos(scored_rows)
    report_rows = group_a + group_b + later + error_rows
    _write_report(output_folder / "ad_scores.csv", report_rows)
    if result:
        for row in report_rows:
            result(row)

    group_folders = {
        "Group_A": output_folder / "Group_A",
        "Group_B": output_folder / "Group_B",
        "To_Be_Used_Later": output_folder / "To_Be_Used_Later",
    }
    _copy_group_videos(input_folder, group_a, group_folders["Group_A"])
    _copy_group_videos(input_folder, group_b, group_folders["Group_B"])
    _copy_group_videos(input_folder, later, group_folders["To_Be_Used_Later"])

    export_jobs = []
    for group_name, group_rows in (("Group_A", group_a), ("Group_B", group_b)):
        for row in group_rows:
            for ratio_key in ratio_keys:
                export_jobs.append((group_name, str(row["file"]), ratio_key))

    total_steps += len(export_jobs)
    if progress:
        progress(done_steps, total_steps)

    for group_name, filename, ratio_key in export_jobs:
        if _cancelled(cancel_event):
            raise ProcessingCancelled()

        source = input_folder / filename
        ratio_folder = group_folders[group_name] / ASPECT_RATIOS[ratio_key].folder_name
        destination = ratio_folder / f"{source.stem}_{ASPECT_RATIOS[ratio_key].folder_name}.mp4"
        try:
            export_video(
                source,
                destination,
                ratio_key,
                detector=detector,
                video_encoder=video_encoder,
                log=log,
                should_cancel=lambda: _cancelled(cancel_event),
            )
        except Exception as exc:
            if log:
                log(f"Export failed for {filename} ({ratio_key}): {exc}")

        done_steps += 1
        if progress:
            progress(done_steps, total_steps)

    if log:
        log(f"Done. Report saved to {output_folder / 'ad_scores.csv'}")
    return report_rows
