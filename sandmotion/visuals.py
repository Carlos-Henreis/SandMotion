"""Visual particle renderer with short, soft motion trails.

The trail is deliberately bounded: it communicates coherent motion without
turning thousands of particles into high-frequency single-pixel flicker.
"""
import numpy as np


def draw_particles(frame: np.ndarray, positions: np.ndarray,
                   velocities: np.ndarray, colors: np.ndarray,
                   size: int = 3) -> np.ndarray:
    if size <= 0:
        raise ValueError("particle size must be positive")
    height, width = frame.shape[:2]

    def stamp(xy: np.ndarray, rgb: np.ndarray, footprint: int) -> None:
        rounded = np.rint(xy).astype(np.int32)
        for dy in range(-(footprint//2), footprint-footprint//2):
            y = rounded[:, 1] + dy
            valid_y = (y>=0)&(y<height)
            for dx in range(-(footprint//2), footprint-footprint//2):
                x = rounded[:, 0] + dx
                good = valid_y&(x>=0)&(x<width)
                frame[y[good], x[good]] = rgb[good]

    # Draw muted motion trails behind the bright particle heads.
    if len(positions):
        for seconds, brightness in ((.032, .22), (.015, .42)):
            shift = np.clip(velocities*seconds, -10, 10)
            trail_colors = np.rint(colors.astype(np.float32)*brightness).astype(np.uint8)
            stamp(positions-shift, trail_colors, max(1, size-1))
    stamp(positions, colors, size)
    return frame
