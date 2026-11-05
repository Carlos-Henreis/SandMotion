import numpy as np
import pytest
from sandmotion.physics import ParticleSystem, plinko_obstacles, release_times


def test_release_gradual_and_reproducible():
    pos = np.array([[10., 10.], [20., 50.], [30., 90.]], dtype=np.float32)
    a = release_times(pos, 42, 48)
    np.testing.assert_array_equal(a, release_times(pos, 42, 48))
    assert a[2] < a[0]
    assert np.all(a >= 0) and np.all(a <= 48)


def test_noise_schedule():
    pos = np.array([[0., 0.], [50., 20.], [100., 90.]], dtype=np.float32)
    times = release_times(pos, 3, 48, "noise")
    assert np.all((times >= 0) & (times <= 48))


def test_inactive_particles_do_not_move():
    p = np.array([[20., 20.], [30., 20.]], dtype=np.float32)
    v = np.zeros((2, 2), dtype=np.float32)
    ps = ParticleSystem(p.copy(), v, np.zeros((2, 3), dtype=np.uint8),
                        gravity=100, drag=0, width=100, floor=95)
    ps.step(.1, active=np.array([True, False]))
    assert ps.positions[0, 1] > 20
    assert ps.positions[1, 1] == 20


def test_terminal_speed():
    ps = ParticleSystem(np.array([[20., 20.]], dtype=np.float32),
                        np.array([[0., 2000.]], dtype=np.float32),
                        np.zeros((1, 3), dtype=np.uint8), gravity=0, drag=0,
                        width=100, floor=95, terminal_speed=120)
    ps.step(.01)
    assert np.linalg.norm(ps.velocities[0]) <= 120.001


def test_invisible_peg_collision():
    ps = ParticleSystem(np.array([[50., 39.]], dtype=np.float32),
                        np.array([[0., 50.]], dtype=np.float32),
                        np.zeros((1, 3), dtype=np.uint8), gravity=0, drag=0,
                        width=100, floor=95, radius=1, obstacles=((50., 50., 8.),))
    ps.step(.1)
    assert np.linalg.norm(ps.positions[0] - np.array([50., 50.])) >= 9 - 1e-4
    assert ps.velocities[0, 1] <= 0


def test_plinko_off():
    assert plinko_obstacles(540, 960, 0) == ()


def test_invalid_release_mode():
    with pytest.raises(ValueError):
        release_times(np.array([[1., 2.]], dtype=np.float32), 42, 10, "unknown")
