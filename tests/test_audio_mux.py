"""Regression: audio mux must never use a different filesystem for rename."""
from pathlib import Path
import subprocess

from sandmotion.narrative import add_audio


def test_mux_uses_destination_directory_and_replaces_original(tmp_path, monkeypatch):
    destination = tmp_path / "out" / "video.mp4"
    destination.parent.mkdir()
    destination.write_bytes(b"video-before-audio")
    calls = []

    def fake_run(cmd, check):
        assert check is True
        mux_path = Path(cmd[-1])
        calls.append(mux_path)
        assert mux_path.parent.parent == destination.parent
        # Same device: atomic os.replace()/Path.replace() can complete.
        assert mux_path.parent.stat().st_dev == destination.parent.stat().st_dev
        assert destination.read_bytes() == b"video-before-audio"
        mux_path.write_bytes(b"video-with-audio")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    add_audio(destination, soundtrack=None, cue=True, duration=60)
    assert len(calls) == 1
    assert destination.read_bytes() == b"video-with-audio"
    assert not calls[0].exists()


def test_mux_failure_does_not_replace_video(tmp_path, monkeypatch):
    destination = tmp_path / "video.mp4"
    destination.write_bytes(b"valid-video")

    def fake_run(cmd, check):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "run", fake_run)
    import pytest
    with pytest.raises(subprocess.CalledProcessError):
        add_audio(destination, soundtrack=None, cue=True, duration=60)
    assert destination.read_bytes() == b"valid-video"
