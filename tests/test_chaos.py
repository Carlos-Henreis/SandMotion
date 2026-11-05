"""Narrative v0.5 timeline and active motion regression tests."""
import numpy as np

from sandmotion.chaos import (
    phase, initial_burst, chaotic_step, rebuild_step, reconstruction_blend,
)


def test_exact_scene_boundaries():
    assert phase(0) == 'hook'
    assert phase(2.999) == 'hook'
    assert phase(3) == 'chaos'
    assert phase(49.999) == 'chaos'
    assert phase(50) == 'rebuild'
    assert phase(56.999) == 'rebuild'
    assert phase(57) == 'hold'
    assert phase(59.999) == 'hold'


def test_burst_is_reproducible_and_spreads():
    rng = np.random.default_rng(3)
    origins = rng.uniform([150, 240], [400, 700], size=(100, 2)).astype(np.float32)
    a = initial_burst(origins, 9, 540, 960)
    b = initial_burst(origins, 9, 540, 960)
    np.testing.assert_array_equal(a, b)
    assert np.mean(np.linalg.norm(a, axis=1)) > 450
    assert a[:, 0].min() < 0 < a[:, 0].max()
    assert a[:, 1].min() < 0 < a[:, 1].max()


def test_particles_do_not_freeze_at_bottom():
    rng = np.random.default_rng(17)
    p = np.column_stack([rng.uniform(25, 515, 200),
                         np.full(200, 956)]).astype(np.float32)
    v = np.zeros_like(p)
    for i in range(300):
        chaotic_step(p, v, 1/60, 30+i/60, 540, 960)
    assert np.std(p[:, 1]) > 10
    assert np.any(p[:, 1] < 900)
    assert np.mean(np.linalg.norm(v, axis=1)) > 50


def test_rebuild_converges_by_57():
    rng = np.random.default_rng(5)
    origins = rng.uniform([30, 50], [510, 900], size=(80, 2)).astype(np.float32)
    p = rng.uniform([0, 0], [540, 960], size=(80, 2)).astype(np.float32)
    v = rng.normal(0, 150, size=(80, 2)).astype(np.float32)
    for i in range(7*120):
        rebuild_step(p, v, origins, 1/120, 50+i/120)
    assert np.percentile(np.linalg.norm(p-origins, axis=1), 95) < 4
    assert reconstruction_blend(50) == 0
    assert reconstruction_blend(57) == 1
