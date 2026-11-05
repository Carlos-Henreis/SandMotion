import numpy as np
from sandmotion.physics import ParticleSystem, explode


def test_gravity_moves_down():
    ps = ParticleSystem(np.array([[10., 10.]], dtype=np.float32), np.zeros((1, 2), dtype=np.float32),
                        np.array([[255, 0, 0]], dtype=np.uint8), gravity=100, drag=0,
                        width=100, floor=90)
    ps.step(0.1)
    assert ps.positions[0, 1] > 10


def test_floor_collision_keeps_particle_inside():
    ps = ParticleSystem(np.array([[20., 85.]], dtype=np.float32),
                        np.array([[0., 100.]], dtype=np.float32),
                        np.array([[255, 0, 0]], dtype=np.uint8), gravity=0, drag=0,
                        width=100, floor=90)
    ps.step(0.2)
    assert ps.positions[0, 1] == 90
    assert ps.velocities[0, 1] <= 0


def test_seed_is_reproducible():
    p = np.array([[10., 10.], [20., 20.]], dtype=np.float32)
    c = np.zeros((2, 3), dtype=np.uint8)
    a = explode(p, c, 123, 500, 900, .2, .35, .74, 100, 90, 1)
    b = explode(p, c, 123, 500, 900, .2, .35, .74, 100, 90, 1)
    np.testing.assert_array_equal(a.velocities, b.velocities)
