from pathlib import Path

import pytest

from meta_video_filter import pipeline


class FakeDetector:
    resolved_device = "cpu"

    def __init__(self, device="auto"):
        self.device = device


def test_pipeline_records_per_video_errors_when_nothing_can_be_scored(tmp_path, monkeypatch):
    input_folder = tmp_path / "input"
    output_folder = input_folder / "Meta_Ad_Output"
    input_folder.mkdir()
    video_path = input_folder / "broken.mp4"
    video_path.write_bytes(b"not a video")

    monkeypatch.setattr(pipeline, "PersonDetector", FakeDetector)
    monkeypatch.setattr(pipeline, "score_video", lambda *args, **kwargs: None)

    received = []
    with pytest.raises(pipeline.PipelineError, match="None of the selected videos could be scored"):
        pipeline.run_pipeline(
            input_folder,
            output_folder,
            ("9:16",),
            result=received.append,
        )

    assert received == [{"file": "broken.mp4", "error": "Could not score video", "group": ""}]
    report = (output_folder / "ad_scores.csv").read_text(encoding="utf-8")
    assert "broken.mp4" in report
    assert "Could not score video" in report
