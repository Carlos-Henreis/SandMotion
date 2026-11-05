"""Screen-filling, bounded chaos and smooth reconstruction for the 60s narrative.

Physics uses fixed dt with bounded velocity; no repeated animation cycles.
"""
import numpy as np

HOOK_END = 3.0
REBUILD_START = 50.0
FINAL_HOLD_START = 57.0
DURATION = 60.0


def phase(t: float, explosion_time: float = HOOK_END) -> str:
    if t < explosion_time:
        return "hook"
    if t < REBUILD_START:
        return "chaos"
    if t < FINAL_HOLD_START:
        return "rebuild"
    return "hold"


def initial_burst(origins: np.ndarray, seed: int, width: int, height: int) -> np.ndarray:
    """A radial explosion that expands across the entire video canvas."""
    rng = np.random.default_rng(seed)
    center = np.array([width * .5, height * .5], dtype=np.float32)
    direction = origins - center
    norm = np.linalg.norm(direction, axis=1, keepdims=True)
    angles = rng.uniform(0, 2*np.pi, len(origins))
    random_direction = np.stack([np.cos(angles), np.sin(angles)], axis=1)
    direction = direction / np.maximum(norm, 1e-6)
    direction = .78*direction + .38*random_direction
    direction /= np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1e-6)
    speeds = rng.uniform(.85, 1.60, (len(origins), 1)) * min(width, height) * 1.7
    return (direction * speeds).astype(np.float32)


def chaotic_step(p: np.ndarray, v: np.ndarray, dt: float, now: float,
                 width: int, height: int, circles=(), ramps=()) -> None:
    """Perpetual bounded motion using moving vortices, stirring and elastic walls.

    No particle settles on the floor: the entire screen is the particle arena.
    """
    px = p[:, 0]
    py = p[:, 1]
    # Time-varying incompressible-ish rotational field, with vertical stirring.
    ax = (210*np.sin(py*.018 + now*1.23) +
          150*np.sin(px*.031 - now*.91))
    ay = (190*np.cos(px*.021 + now*.87) -
          135*np.sin(py*.024 - now*1.49))
    # Floating moving vortex centres. Acceleration is tangential, not an
    # unconditional push to the bottom of the scene.
    cx = width*(.5 + .21*np.sin(now*.29))
    cy = height*(.5 + .19*np.cos(now*.33))
    delta_x = px-cx
    delta_y = py-cy
    ax -= .43*delta_y
    ay += .43*delta_x
    # Repel walls before impact so no long-lived boundary piles form.
    margin = max(12., width*.055)
    ax += 650*np.clip((margin-px)/margin, 0, 1)
    ax -= 650*np.clip((px-(width-margin))/margin, 0, 1)
    ay += 700*np.clip((margin-py)/margin, 0, 1)
    ay -= 700*np.clip((py-(height-margin))/margin, 0, 1)
    v[:, 0] += ax*dt
    v[:, 1] += ay*dt
    v *= np.exp(-.14*dt)
    speed = np.linalg.norm(v, axis=1)
    # Keep a minimum drift so a few balanced particles never look frozen.
    low = speed < 85.
    if np.any(low):
        angle = (px[low]*.019 + py[low]*.027 + now*.47)
        v[low, 0] += 95*np.cos(angle)*dt*4
        v[low, 1] += 95*np.sin(angle)*dt*4
    cap = max(width, height)*1.75
    v *= np.minimum(1., cap/np.maximum(np.linalg.norm(v, axis=1), 1e-8))[:, None]
    p += v*dt

    # Invisible circular pegs are active throughout the chaotic phase.
    for cx, cy, radius in circles:
        offset = p - (cx, cy)
        dist = np.linalg.norm(offset, axis=1)
        hit = dist < radius+2
        if not np.any(hit):
            continue
        normal = offset[hit]/np.maximum(dist[hit, None], 1e-6)
        normal[dist[hit] < 1e-6] = (0., -1.)
        p[hit] = (cx, cy)+normal*(radius+2)
        vel = v[hit]
        incoming = np.minimum(np.sum(vel*normal, axis=1), 0)
        vel -= 1.65*incoming[:, None]*normal
        # Deterministic perpendicular kick avoids predictable straight columns.
        tangent = np.stack([-normal[:, 1], normal[:, 0]], axis=1)
        vel += 60*tangent*np.sin(now*4+cx*.01)
        v[hit] = vel

    # Slanted ramps scatter passing streams rather than trapping them.
    for a, b in ramps:
        a, b = np.asarray(a), np.asarray(b)
        ab = b-a
        u = np.clip(((p-a)@ab)/(ab@ab), 0, 1)
        closest = a + u[:, None]*ab
        diff = p-closest
        dist = np.linalg.norm(diff, axis=1)
        hit = dist < 3
        if not np.any(hit):
            continue
        normal = diff[hit]/np.maximum(dist[hit, None], 1e-6)
        normal[dist[hit] < 1e-6] = (0., -1.)
        p[hit] = closest[hit]+3*normal
        vel = v[hit]
        incoming = np.minimum(np.sum(vel*normal, axis=1), 0)
        vel -= 1.55*incoming[:, None]*normal
        v[hit] = vel

    # Reflect on all four edges; critically, do NOT clamp velocity to zero.
    left = p[:, 0] < 1
    right = p[:, 0] > width-2
    top = p[:, 1] < 1
    bottom = p[:, 1] > height-2
    p[:, 0] = np.clip(p[:, 0], 1, width-2)
    p[:, 1] = np.clip(p[:, 1], 1, height-2)
    v[left & (v[:, 0]<0), 0] *= -.94
    v[right & (v[:, 0]>0), 0] *= -.94
    v[top & (v[:, 1]<0), 1] *= -.94
    v[bottom & (v[:, 1]>0), 1] *= -.94


def rebuild_step(p: np.ndarray, v: np.ndarray, origins: np.ndarray,
                 dt: float, now: float) -> None:
    """Smoothly home to exact original positions between 50 and 57 seconds."""
    u = np.clip((now-REBUILD_START)/(FINAL_HOLD_START-REBUILD_START), 0, 1)
    smooth = u*u*(3-2*u)
    stiffness = 5+95*smooth
    damping = 5+19*smooth
    v += (stiffness*(origins-p)-damping*v)*dt
    p += v*dt


def reconstruction_blend(now: float) -> float:
    """Fade dense raster back in before 57s, hiding particle sampling holes."""
    u = np.clip((now-54.5)/2.5, 0, 1)
    return float(u*u*(3-2*u))
