"""Soundscape timing, silence and speed regression tests."""
import numpy as np
import pytest
from sandmotion.soundscape import soundscape, soundscape_wave
from sandmotion.narrative import render_narrative


def rms(x):
    return float(np.sqrt(np.mean(np.square(x.astype(np.float64)))))


def test_sound_events_follow_visual_timeline():
    rate = 4000
    data = soundscape(60, seed=7, sample_rate=rate)
    assert len(data) == 60*rate
    assert rms(data[:2*rate]) == 0
    assert rms(data[round(3.02*rate):round(3.20*rate)]) > 0.01
    assert rms(data[20*rate:21*rate]) > 0.001
    assert rms(data[50*rate:51*rate]) > 0.01
    assert rms(data[58*rate:59*rate]) > 0


def test_sound_is_repeatable_and_bounded(tmp_path):
    a = soundscape(60, seed=42, sample_rate=3000)
    b = soundscape(60, seed=42, sample_rate=3000)
    np.testing.assert_array_equal(a, b)
    assert np.max(np.abs(a)) <= .95
    output = tmp_path/'effects.wav'
    soundscape_wave(output, duration=60, sample_rate=3000)
    assert output.stat().st_size > 60*3000*2


def test_motion_speed_rejects_invalid_values(tmp_path):
    with pytest.raises(ValueError, match='motion-speed'):
        render_narrative(tmp_path/'missing.png', tmp_path/'out.mp4',
                         width=64, height=96, fps=2, duration=60,
                         count=5, seed=2, particle_size=1, crf=30,
                         motion_speed=0.0)
