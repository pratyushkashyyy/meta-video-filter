import csv
from pathlib import Path

from meta_video_filter import pipeline


class FakeDetector:
    resolved_device = "cpu"

    def __init__(self, device="auto"):
        self.device = device


class FakeScore:
    def __init__(self, path: Path):
        self.path = path

    def to_dict(self):
        score = int(self.path.stem.replace("video_", ""))
        return {"file": self.path.name, "final_score": score}


def test_pipeline_exports_numbered_files_without_copying_originals(tmp_path, monkeypatch):
    input_folder = tmp_path / "input"
    output_folder = input_folder / "Meta_Ad_Output"
    input_folder.mkdir()
    video_paths = []
    for index in range(4):
        video_path = input_folder / f"video_{index}.mp4"
        video_path.write_bytes(b"source")
        video_paths.append(video_path)

    exported = []

    def fake_export_video(input_path, output_path, *args, **kwargs):
        exported.append((Path(input_path).name, Path(output_path)))
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"export")

    monkeypatch.setattr(pipeline, "PersonDetector", FakeDetector)
    monkeypatch.setattr(pipeline, "iter_video_files", lambda *args: video_paths)
    monkeypatch.setattr(pipeline, "score_video", lambda path, **kwargs: FakeScore(path))
    monkeypatch.setattr(pipeline, "save_thumbnail", lambda *args: None)
    monkeypatch.setattr(pipeline, "export_video", fake_export_video)

    rows = pipeline.run_pipeline(
        input_folder,
        output_folder,
        ("9:16",),
        group_count=2,
        videos_per_group=2,
    )

    assert [path.name for _, path in exported] == ["1.mp4", "2.mp4", "1.mp4", "2.mp4"]
    assert (output_folder / "Group_A" / "9x16" / "1.mp4").exists()
    assert (output_folder / "Group_B" / "9x16" / "2.mp4").exists()
    assert not (output_folder / "Group_A" / "video_3.mp4").exists()
    assert rows[0]["file"] == "video_3.mp4"
    assert rows[0]["export_file"] == "1.mp4"

    with (output_folder / "ad_scores.csv").open(encoding="utf-8") as file:
        report_rows = list(csv.DictReader(file))
    assert report_rows[0]["file"] == "video_3.mp4"
    assert report_rows[0]["export_index"] == "1"
    assert report_rows[0]["export_file"] == "1.mp4"
