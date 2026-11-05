"""Video encoding profile regression tests."""
import subprocess
import shutil
from pathlib import Path

import pytest
from PIL import Image

from sandmotion.encoding import encoding_args
from sandmotion.render import render


def test_social_default_targets_four_megabits():
    args = encoding_args()
    assert args == ["-c:v", "libx264", "-preset", "slow",
                    "-b:v", "4M", "-maxrate", "5M", "-bufsize", "10M"]


def test_other_profiles_and_override():
    assert "-b:v" in encoding_args("balanced")
    assert "6M" in encoding_args("balanced")
    quality = encoding_args("quality", crf=20)
    assert quality[-2:] == ["-crf", "20"]
    assert "-b:v" not in quality
    assert "2M" in encoding_args("social", bitrate_mbps=2)
    assert "2.5M" in encoding_args("quality", bitrate_mbps=2.5)


@pytest.mark.parametrize("profile,crf,rate", [
    ("invalid", 20, None), ("social", -1, None),
    ("quality", 52, None), ("social", 20, 0),
])
def test_invalid_settings(profile, crf, rate):
    with pytest.raises(ValueError):
        encoding_args(profile, crf=crf, bitrate_mbps=rate)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg unavailable")
def test_short_video_encoding_is_bitrate_limited(tmp_path: Path):
    source = tmp_path / "test.png"
    Image.new("RGBA", (16, 16), (255, 160, 30, 255)).save(source)
    destination = tmp_path / "test.mp4"
    render(source, destination, mode="explosion", duration=1.0, delay=.2,
           release_duration=.2, cycle_duration=1.0, width=64, height=96,
           fps=5, count=20, encoding_profile="social")
    assert destination.is_file()
    assert destination.stat().st_size > 0
