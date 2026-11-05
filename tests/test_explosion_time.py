"""Configurable explosion timestamp regression tests."""
import numpy as np
import pytest
from sandmotion.chaos import phase
from sandmotion.soundscape import soundscape
from sandmotion.narrative import render_narrative


@pytest.mark.parametrize("explosion_time", [0, 1.5, 3, 6, 12, 49.5])
def test_visual_timeline_follows_explosion_time(explosion_time):
    if explosion_time > 0:
        assert phase(explosion_time-0.001, explosion_time) == "hook"
    assert phase(explosion_time, explosion_time) == "chaos"
    assert phase(50, explosion_time) == "rebuild"
    assert phase(57, explosion_time) == "hold"


def test_explosion_audio_shifts_with_visual_timing():
    rate = 4000
    sound = soundscape(duration=60, seed=2, sample_rate=rate, explosion_time=6)
    assert np.max(np.abs(sound[:6*rate])) == 0
    assert np.max(np.abs(sound[round(6.05*rate):round(6.15*rate)])) > .01
    assert np.any(sound[30*rate:31*rate] != 0)
    assert np.any(sound[50*rate:51*rate] != 0)


@pytest.mark.parametrize("invalid", [-1, 50, 60])
def test_explosion_time_rejects_invalid_values(invalid, tmp_path):
    with pytest.raises(ValueError, match="explosion-time"):
        render_narrative(tmp_path/"unneeded.png", tmp_path/"out.mp4",
                         width=64, height=96, fps=2, duration=60,
                         count=5, seed=1, particle_size=1, crf=20,
                         explosion_time=invalid)
