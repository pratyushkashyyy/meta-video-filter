import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from meta_video_filter.scoring import calc_brightness, calc_motion, calc_sharpness, detect_text_overlay_opencv


def test_calc_brightness():
    frame = np.full((20, 20, 3), 120, dtype=np.uint8)
    assert calc_brightness(frame) == 120


def test_calc_motion():
    first = np.zeros((10, 10), dtype=np.uint8)
    second = np.full((10, 10), 25, dtype=np.uint8)
    assert calc_motion(first, second) == 25


def test_calc_sharpness_flat_frame_is_zero():
    frame = np.full((20, 20, 3), 120, dtype=np.uint8)
    assert calc_sharpness(frame) == 0


def test_text_overlay_detector_runs():
    frame = np.zeros((180, 320, 3), dtype=np.uint8)
    cv2.putText(frame, "SALE SALE SALE", (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    assert detect_text_overlay_opencv(frame) in (0, 1)
