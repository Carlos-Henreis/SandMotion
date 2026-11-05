from pathlib import Path

import numpy as np
from PIL import Image

from sandmotion.render import load_centered_rgb, image_particles, draw_frame


def test_clean_preview_uses_full_raster(tmp_path: Path):
    image = Image.new("RGBA", (16, 16), (240, 50, 20, 255))
    image.save(tmp_path / "input.png")
    preview = load_centered_rgb(tmp_path / "input.png", 80, 80)
    positions, colors = image_particles(tmp_path / "input.png", 80, 80, 5, seed=42)
    particles = np.frombuffer(draw_frame(80, 80, positions, colors, 1), dtype=np.uint8).reshape((80, 80, 3))
    # Full raster preview is intact regardless of particle count.
    assert tuple(preview[40, 40]) == (240, 50, 20)
    assert np.count_nonzero(np.all(preview == (240, 50, 20), axis=2)) > 100
    assert np.count_nonzero(np.all(particles == (240, 50, 20), axis=2)) <= 5


def test_transparent_background_is_composited(tmp_path: Path):
    image = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    image.putpixel((5, 5), (255, 255, 255, 255))
    image.save(tmp_path / "alpha.png")
    preview = load_centered_rgb(tmp_path / "alpha.png", 80, 80)
    assert tuple(preview[0, 0]) == (12, 14, 23)
    assert np.any(np.all(preview == (255, 255, 255), axis=2))
