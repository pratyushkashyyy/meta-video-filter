from meta_video_filter import dependencies


def test_bundled_or_path_executable_uses_imageio_fallback(monkeypatch, tmp_path):
    executable = tmp_path / "ffmpeg"
    executable.write_bytes(b"binary")

    class FakeImageIOFfmpeg:
        @staticmethod
        def get_ffmpeg_exe():
            return str(executable)

    monkeypatch.setattr(dependencies, "imageio_ffmpeg", FakeImageIOFfmpeg)
    monkeypatch.setattr(dependencies.shutil, "which", lambda _: None)

    assert dependencies.find_bundled_or_path_executable("not-on-path") == str(executable)
