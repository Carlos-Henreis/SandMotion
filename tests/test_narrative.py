"""Narrative physics and rendering regression tests."""
from pathlib import Path
import shutil
import subprocess

import numpy as np
import pytest
from PIL import Image

from sandmotion.narrative import (
    sweep_order, funnel_geometry, narrative_step, draw_narrative,
    cue_wave, render_narrative,
)


def test_organic_sweep_roughly_left_to_right():
    x = np.array([2., 30., 60., 100.])
    y = np.full_like(x, 20.)
    order = sweep_order(x, y, 120, seed=42)
    assert order[0] < order[-1]
    np.testing.assert_array_equal(order, sweep_order(x, y, 120, seed=42))


def test_funnel_geometry_contains_circles_and_ramps():
    circles, ramps = funnel_geometry(540, 960)
    assert len(circles) == 5
    assert len(ramps) == 2


def test_return_moves_toward_origin():
    origin = np.array([[50., 30.]], dtype=np.float32)
    p = np.array([[30., 80.]], dtype=np.float32)
    v = np.zeros_like(p)
    for _ in range(100):
        narrative_step(p, v, origin, np.array([True]), .02, 57,
                       100, 100, (), ())
    assert np.linalg.norm(p-origin) < 3


def test_raster_reconstruction_is_complete():
    base = np.zeros((8, 8, 3), dtype=np.uint8)
    rgb = np.full((8, 8, 3), (20, 50, 80), dtype=np.uint8)
    alpha = np.full((8, 8), 255, dtype=np.uint8)
    order = np.ones((8, 8), dtype=np.float32)
    frame = draw_narrative(base, rgb, alpha, order,
                           np.array([[3., 3.]], dtype=np.float32),
                           np.array([[20, 50, 80]], dtype=np.uint8),
                           np.array([True]), 1, 1, return_blend=1)
    actual = np.frombuffer(frame, dtype=np.uint8).reshape((8, 8, 3))
    np.testing.assert_array_equal(actual, rgb)


def test_audio_cue_is_created(tmp_path):
    filename = tmp_path / 'cue.wav'
    cue_wave(filename)
    assert filename.stat().st_size > 50000


@pytest.mark.skipif(shutil.which('ffmpeg') is None or shutil.which('ffprobe') is None,
                    reason='FFmpeg não instalado')
def test_integration_renders_one_minute_with_audio(tmp_path: Path):
    inp = tmp_path / 'sample.png'
    Image.new('RGBA', (16, 16), (20, 200, 80, 255)).save(inp)
    out = tmp_path / 'narrative.mp4'
    render_narrative(inp, out, width=64, height=96, fps=2, duration=60,
                     count=50, seed=1, particle_size=1, crf=30, drop_sound=True)
    probe = subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries',
        'format=duration:stream=codec_type', '-of', 'default=noprint_wrappers=1',
        str(out)], text=True)
    assert 'codec_type=video' in probe
    assert 'codec_type=audio' in probe
    assert abs(float(next(line.split('=')[1] for line in probe.splitlines()
                          if line.startswith('duration='))) - 60) < .1
