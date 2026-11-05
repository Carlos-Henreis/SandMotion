"""Image clarity tests for the high-quality 720p vertical render."""
import numpy as np
from PIL import Image
from sandmotion.render import load_image, image_particles
from sandmotion.visuals import draw_particles
from sandmotion.chaos import reconstruction_blend


def test_artwork_uses_more_of_canvas(tmp_path):
    source = tmp_path/"image.png"
    Image.new("RGBA", (800, 450), (20, 120, 240, 255)).save(source)
    picture = load_image(source, 720, 1280)
    assert picture.width >= 680
    assert picture.height >= 380
    positions, colors = image_particles(source, 720, 1280, 100, 9)
    assert np.max(positions[:, 0]) <= 720
    assert len(colors) == 100


def test_render_particle_trails_and_head():
    frame = np.zeros((80, 80, 3), dtype=np.uint8)
    positions = np.array([[40, 40]], dtype=np.float32)
    velocities = np.array([[120, 0]], dtype=np.float32)
    colors = np.array([[200, 50, 30]], dtype=np.uint8)
    output = draw_particles(frame, positions, velocities, colors, size=3)
    np.testing.assert_array_equal(output[40,40], colors[0])
    assert output[40,36].sum() > 0
    assert output[10,10].sum() == 0


def test_return_fade_progressively_cleans_image():
    assert reconstruction_blend(52) == 0
    assert 0 < reconstruction_blend(55) < 1
    assert reconstruction_blend(57) == 1
