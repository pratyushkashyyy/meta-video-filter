from __future__ import annotations

import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

import cv2
import numpy as np

from .dependencies import find_bundled_or_path_executable


def bundled_yolo_model_path() -> str:
    """Use the model included with installers; source runs retain Ultralytics' fallback."""
    model_path = Path(__file__).with_name("assets") / "models" / "yolov8n.pt"
    if model_path.exists():
        return str(model_path)
    return "yolov8n.pt"

ProgressCallback = Callable[[str], None]
CancelCallback = Callable[[], bool]


@dataclass
class ScoreResult:
    file: str
    final_score: float
    hook_motion: float
    motion_avg: float
    scene_cuts: int
    text_overlay_hits: int
    person_hits: int
    brightness: float
    sharpness: float
    audio_rms: float
    audio_spike: float
    static_intro_penalty: int
    group: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class PersonDetector:
    """Lazy YOLO wrapper so the model is loaded only when work starts."""

    def __init__(self, model_path: str | None = None, device: str = "auto") -> None:
        self.model_path = model_path or bundled_yolo_model_path()
        self.device = device
        self._model = None
        self._resolved_device = None

    @property
    def model(self):
        if self._model is None:
            from ultralytics import YOLO

            self._model = YOLO(self.model_path)
        return self._model

    @property
    def resolved_device(self) -> str:
        if self._resolved_device is None:
            self._resolved_device = resolve_yolo_device(self.device)
        return self._resolved_device

    def detect_person(self, frame) -> int:
        return 1 if self.detect_person_boxes(frame) else 0

    def detect_person_boxes(self, frame) -> list[tuple[float, float, float, float, float]]:
        boxes: list[tuple[float, float, float, float, float]] = []
        results = self.model(frame, verbose=False, device=self.resolved_device)
        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                if cls != 0:
                    continue
                confidence = float(box.conf[0]) if box.conf is not None else 1.0
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
                boxes.append((x1, y1, x2, y2, confidence))
        return boxes


def resolve_yolo_device(device: str = "auto") -> str:
    """Return the YOLO device string, preferring CUDA only when PyTorch can use it."""
    if device != "auto":
        return device

    env_device = os.getenv("META_VIDEO_FILTER_DEVICE")
    if env_device:
        return env_device

    try:
        import torch

        if torch.cuda.is_available():
            return "cuda:0"
    except Exception:
        pass

    return "cpu"


def calc_sharpness(frame) -> float:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def calc_brightness(frame) -> float:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def calc_motion(prev_gray, gray) -> float:
    diff = cv2.absdiff(prev_gray, gray)
    return float(np.mean(diff))


def scene_cut_score(prev_hist, hist) -> float:
    return float(cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA))


def detect_text_overlay_opencv(frame) -> int:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blur, 60, 180)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = gray.shape[:2]
    text_like_boxes = 0

    for cnt in contours:
        _, y, cw, ch = cv2.boundingRect(cnt)
        if cw < 20 or ch < 8:
            continue
        if cw > w * 0.9 or ch > h * 0.4:
            continue

        aspect = cw / (ch + 1e-6)
        if aspect > 2.5 and cw > w * 0.2:
            text_like_boxes += 1
        if y > h * 0.55 and cw > w * 0.25 and ch < h * 0.12:
            text_like_boxes += 2

    return 1 if text_like_boxes >= 3 else 0


def get_audio_features(
    video_path: str | Path,
    log: ProgressCallback | None = None,
    sample_rate: int = 22050,
) -> tuple[float, float]:
    """Return RMS loudness and peak/RMS ratio using ffmpeg-decoded mono PCM."""
    ffmpeg = find_bundled_or_path_executable("ffmpeg", "ffmpeg.exe")
    if not ffmpeg:
        if log:
            log("Audio analysis skipped: ffmpeg was not found on PATH.")
        return 0.0, 0.0

    command = [
        ffmpeg,
        "-v",
        "error",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-f",
        "f32le",
        "pipe:1",
    ]

    try:
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode != 0:
            message = completed.stderr.decode("utf-8", errors="replace").strip()
            if log:
                log(f"Audio analysis failed for {Path(video_path).name}: {message or 'ffmpeg decode failed'}")
            return 0.0, 0.0

        if not completed.stdout:
            return 0.0, 0.0

        audio = np.frombuffer(completed.stdout, dtype=np.float32)
        if audio.size == 0:
            return 0.0, 0.0

        rms = float(np.sqrt(np.mean(audio**2)))
        peak = float(np.max(np.abs(audio)))
        spike_ratio = peak / (rms + 1e-6)
        return rms, float(spike_ratio)
    except Exception as exc:
        if log:
            log(f"Audio analysis failed for {Path(video_path).name}: {exc}")
        return 0.0, 0.0


def save_thumbnail(video_path: str | Path, out_path: str | Path) -> bool:
    cap = cv2.VideoCapture(str(video_path))
    try:
        cap.set(cv2.CAP_PROP_POS_MSEC, 1000)
        ret, frame = cap.read()
        if ret:
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            return bool(cv2.imwrite(str(out_path), frame))
        return False
    finally:
        cap.release()


def iter_video_files(folder: str | Path, extensions: Iterable[str]) -> list[Path]:
    base = Path(folder)
    return sorted(
        path
        for path in base.iterdir()
        if path.is_file() and path.suffix.lower() in tuple(ext.lower() for ext in extensions)
    )


def score_video(
    video_path: str | Path,
    detector: PersonDetector | None = None,
    log: ProgressCallback | None = None,
    should_cancel: CancelCallback | None = None,
) -> ScoreResult | None:
    video_path = Path(video_path)
    detector = detector or PersonDetector()
    cap = cv2.VideoCapture(str(video_path))

    try:
        if not cap.isOpened():
            if log:
                log(f"Could not open {video_path.name}")
            return None

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30

        frames_to_check = int(fps * 4)
        prev_gray = None
        prev_hist = None

        motion_total = 0.0
        motion_first1s = 0.0
        brightness_total = 0.0
        sharpness_total = 0.0
        motion_frames = 0
        hook_motion_frames = 0
        cut_count = 0
        text_hits = 0
        person_hits = 0
        frames_read = 0

        for i in range(frames_to_check):
            if should_cancel and should_cancel():
                return None

            ret, frame = cap.read()
            if not ret:
                break

            frames_read += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness_total += calc_brightness(frame)
            sharpness_total += calc_sharpness(frame)

            if prev_gray is not None:
                motion = calc_motion(prev_gray, gray)
                motion_total += motion
                motion_frames += 1
                if i < int(fps * 1.2):
                    motion_first1s += motion
                    hook_motion_frames += 1

            prev_gray = gray
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()

            if prev_hist is not None and scene_cut_score(prev_hist, hist) > 0.6:
                cut_count += 1
            prev_hist = hist

            if i % 10 == 0:
                text_hits += detect_text_overlay_opencv(frame)
            if i % 18 == 0:
                person_hits += detector.detect_person(frame)

        if frames_read == 0:
            return None

        motion_avg = motion_total / max(1, motion_frames)
        motion_hook = motion_first1s / max(1, hook_motion_frames)
        brightness_avg = brightness_total / frames_read
        sharpness_avg = sharpness_total / frames_read
        static_intro_penalty = 20 if motion_hook < 4.5 else 0
        audio_rms, audio_spike = get_audio_features(video_path, log=log)

        brightness_score = min(max((brightness_avg - 50) / 150, 0), 1) * 10
        sharpness_score = min(max(sharpness_avg / 500, 0), 1) * 10
        motion_score = min(max(motion_avg / 15, 0), 1) * 25
        hook_score = min(max(motion_hook / 15, 0), 1) * 30
        cut_score = min(cut_count, 12) * 2.0
        text_score = min(text_hits, 10) * 2.5
        person_score = min(person_hits, 6) * 3.0
        audio_score = min(audio_rms * 100, 10) + min(audio_spike, 8)

        final_score = (
            hook_score
            + motion_score
            + cut_score
            + text_score
            + person_score
            + brightness_score
            + sharpness_score
            + audio_score
        ) - static_intro_penalty

        return ScoreResult(
            file=os.path.basename(video_path),
            final_score=round(float(final_score), 2),
            hook_motion=round(float(motion_hook), 2),
            motion_avg=round(float(motion_avg), 2),
            scene_cuts=cut_count,
            text_overlay_hits=text_hits,
            person_hits=person_hits,
            brightness=round(float(brightness_avg), 2),
            sharpness=round(float(sharpness_avg), 2),
            audio_rms=round(float(audio_rms), 4),
            audio_spike=round(float(audio_spike), 2),
            static_intro_penalty=static_intro_penalty,
        )
    finally:
        cap.release()
