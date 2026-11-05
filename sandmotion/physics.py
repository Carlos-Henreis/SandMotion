"""Vectorized particles with gravity, speed limiting and invisible Plinko pegs."""
from dataclasses import dataclass, field
import numpy as np


@dataclass
class ParticleSystem:
    positions: np.ndarray
    velocities: np.ndarray
    colors: np.ndarray
    gravity: float = 900.0
    drag: float = 0.22
    bounce: float = 0.35
    friction: float = 0.74
    floor: float = 900.0
    width: int = 540
    radius: int = 1
    terminal_speed: float = 320.0
    obstacles: tuple[tuple[float, float, float], ...] = field(default_factory=tuple)

    def step(self, dt: float, active: np.ndarray | None = None) -> None:
        """Advance only released particles; never disturb particles still in the image."""
        if active is None:
            ids = np.arange(len(self.positions))
        else:
            ids = np.flatnonzero(active)
        if not len(ids):
            return
        p = self.positions[ids].copy()
        v = self.velocities[ids].copy()
        v[:, 1] += self.gravity * dt
        v *= np.exp(-self.drag * dt)
        speed = np.linalg.norm(v, axis=1)
        factor = np.minimum(1.0, self.terminal_speed / np.maximum(speed, 1e-7))
        v *= factor[:, None]
        p += v * dt

        # Static circular colliders (not drawn). Displace penetrations and reflect
        # inward-moving velocities along the surface normal.
        for cx, cy, r in self.obstacles:
            delta = p - np.array((cx, cy), dtype=p.dtype)
            distances = np.linalg.norm(delta, axis=1)
            hit = distances < r + self.radius
            if not np.any(hit):
                continue
            normal = delta[hit] / np.maximum(distances[hit, None], 1e-6)
            degenerate = distances[hit] < 1e-6
            normal[degenerate] = (0.0, -1.0)
            p[hit] = np.array((cx, cy)) + normal * (r + self.radius)
            incoming = np.sum(v[hit] * normal, axis=1)
            vhit = v[hit]
            vhit -= np.minimum(incoming, 0.0)[:, None] * (1.0 + self.bounce) * normal
            v[hit] = vhit

        left = p[:, 0] < self.radius
        right = p[:, 0] > self.width - 1 - self.radius
        p[left, 0] = self.radius
        p[right, 0] = self.width - 1 - self.radius
        v[left & (v[:, 0] < 0), 0] *= -self.bounce
        v[right & (v[:, 0] > 0), 0] *= -self.bounce

        landed = p[:, 1] >= self.floor
        p[landed, 1] = self.floor
        hitting = landed & (v[:, 1] > 0)
        v[hitting, 1] *= -self.bounce
        v[landed, 0] *= self.friction ** (dt * 30.0)
        resting = landed & (np.abs(v[:, 1]) < 35)
        v[resting, 1] = 0
        self.positions[ids] = p
        self.velocities[ids] = v


def plinko_obstacles(width: int, height: int, rows: int = 4) -> tuple[tuple[float, float, float], ...]:
    """Invisible staggered pegs under the artwork (no sprites are rendered)."""
    if rows <= 0:
        return ()
    spacing = width / 6
    radius = max(5.0, min(width, height) * 0.015)
    pegs = []
    for row in range(rows):
        cy = height * (0.79 + row * 0.038)
        if cy + radius >= height - 2:
            break
        for column in range(1, 6):
            cx = spacing * (column + (0.5 if row % 2 else 0.0))
            if cx + radius < width:
                pegs.append((float(cx), float(cy), float(radius)))
    return tuple(pegs)


def release_times(positions: np.ndarray, seed: int, duration: float,
                  mode: str = "bottom-up") -> np.ndarray:
    """Stable times in [0,duration], with noise that spreads the disintegration."""
    if duration <= 0:
        raise ValueError("release duration must be > 0")
    if mode not in ("bottom-up", "noise"):
        raise ValueError("release mode must be bottom-up or noise")
    rng = np.random.default_rng(seed + 17)
    x = positions[:, 0]
    y = positions[:, 1]
    yspan = max(float(np.ptp(y)), 1.0)
    bottom_first = (float(np.max(y)) - y) / yspan
    # Multi-scale smooth spatial variation without an extra Perlin dependency.
    wave = (np.sin(x * 0.034 + y * 0.021 + seed) +
            np.sin(x * 0.071 - y * 0.043 + seed * 0.17)) / 4 + 0.5
    jitter = rng.random(len(positions))
    if mode == "bottom-up":
        order = 0.76 * bottom_first + 0.17 * wave + 0.07 * jitter
    else:
        order = 0.80 * wave + 0.20 * jitter
    order -= order.min()
    order /= max(float(order.max()), 1e-8)
    return (order * duration).astype(np.float32)


def explode(positions: np.ndarray, colors: np.ndarray, seed: int,
            force: float, gravity: float, drag: float, bounce: float,
            friction: float, width: int, floor: int, radius: int,
            terminal_speed: float = 320.0,
            obstacles: tuple[tuple[float, float, float], ...] = ()) -> ParticleSystem:
    rng = np.random.default_rng(seed)
    center = positions.mean(axis=0)
    direction = positions - center
    norm = np.linalg.norm(direction, axis=1, keepdims=True)
    direction /= np.maximum(norm, 0.0001)
    angles = rng.uniform(0, 2 * np.pi, len(positions))
    jitter = np.stack([np.cos(angles), np.sin(angles)], axis=1)
    strength = rng.uniform(0.48, 1.18, (len(positions), 1))
    velocities = force * strength * (0.82 * direction + 0.25 * jitter)
    velocities[:, 1] -= force * 0.22
    return ParticleSystem(positions.copy(), velocities, colors.copy(),
                          gravity, drag, bounce, friction, floor, width, radius,
                          terminal_speed, obstacles)
