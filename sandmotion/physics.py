"""Vectorized independent-particle simulation in screen-space pixels."""
from dataclasses import dataclass
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

    def step(self, dt: float) -> None:
        # Semi-implicit Euler, pixels/second; screen y grows downwards.
        self.velocities[:, 1] += self.gravity * dt
        self.velocities *= np.exp(-self.drag * dt)
        self.positions += self.velocities * dt

        low = self.positions[:, 0] < self.radius
        high = self.positions[:, 0] > self.width - 1 - self.radius
        self.positions[low, 0] = self.radius
        self.positions[high, 0] = self.width - 1 - self.radius
        self.velocities[low & (self.velocities[:, 0] < 0), 0] *= -self.bounce
        self.velocities[high & (self.velocities[:, 0] > 0), 0] *= -self.bounce

        landed = self.positions[:, 1] >= self.floor
        self.positions[landed, 1] = self.floor
        hitting = landed & (self.velocities[:, 1] > 0)
        self.velocities[hitting, 1] *= -self.bounce
        self.velocities[landed, 0] *= self.friction ** (dt * 30.0)
        # Suppress jitter and keep resting particles on the floor.
        resting = landed & (np.abs(self.velocities[:, 1]) < 35)
        self.velocities[resting, 1] = 0


def explode(positions: np.ndarray, colors: np.ndarray, seed: int,
            force: float, gravity: float, drag: float, bounce: float,
            friction: float, width: int, floor: int, radius: int) -> ParticleSystem:
    rng = np.random.default_rng(seed)
    center = positions.mean(axis=0)
    direction = positions - center
    norm = np.linalg.norm(direction, axis=1, keepdims=True)
    direction /= np.maximum(norm, 0.0001)
    angles = rng.uniform(0, 2 * np.pi, len(positions))
    jitter = np.stack([np.cos(angles), np.sin(angles)], axis=1)
    strength = rng.uniform(0.48, 1.18, (len(positions), 1))
    # Mix radial trajectory and random turbulence; mild upward impulse.
    velocities = force * strength * (0.82 * direction + 0.25 * jitter)
    velocities[:, 1] -= force * 0.22
    return ParticleSystem(positions.copy(), velocities, colors.copy(),
                          gravity, drag, bounce, friction, floor, width, radius)
