"""Load the image, scatter pixels, and stream frames to FFmpeg."""
import shutil
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from .physics import explode


def image_particles(path: Path, width: int, height: int, max_particles: int,
                    seed: int) -> tuple[np.ndarray, np.ndarray]:
    rgba = Image.open(path).convert("RGBA")
    rgba.thumbnail((int(width * 0.75), int(height * 0.54)), Image.Resampling.LANCZOS)
    arr = np.asarray(rgba)
    coords = np.argwhere(arr[:, :, 3] >= 64)
    if not len(coords):
        raise ValueError("A imagem não possui pixels visíveis (alpha >= 64).")
    rng = np.random.default_rng(seed)
    if len(coords) > max_particles:
        coords = coords[rng.choice(len(coords), max_particles, replace=False)]
    ys, xs = coords[:, 0], coords[:, 1]
    positions = np.column_stack([xs + (width - rgba.width) / 2,
                                 ys + (height - rgba.height) / 2]).astype(np.float32)
    colors = arr[ys, xs, :3].copy()
    return positions, colors


def draw_frame(width: int, height: int, positions: np.ndarray,
               colors: np.ndarray, size: int, background=(12, 14, 23)) -> bytes:
    frame = np.empty((height, width, 3), dtype=np.uint8)
    frame[:] = background
    coords = np.rint(positions).astype(np.int32)
    # Colored square sprites. Renderer can be replaced without touching physics.
    for dy in range(-(size // 2), size - size // 2):
        for dx in range(-(size // 2), size - size // 2):
            x = coords[:, 0] + dx
            y = coords[:, 1] + dy
            valid = (x >= 0) & (x < width) & (y >= 0) & (y < height)
            frame[y[valid], x[valid]] = colors[valid]
    return frame.tobytes()


def render(input_path: Path, output_path: Path, *, width: int = 540,
           height: int = 960, fps: int = 30, duration: float = 8.0,
           delay: float = 1.0, count: int = 30000, force: float = 650.0,
           gravity: float = 900.0, drag: float = 0.22, bounce: float = 0.35,
           friction: float = 0.74, seed: int = 42, particle_size: int = 2,
           crf: int = 20) -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg não encontrado. Instale com: sudo apt install ffmpeg")
    if min(width, height, fps, count, particle_size) <= 0 or duration <= 0 or delay < 0 or delay >= duration:
        raise ValueError("Verifique resolução, FPS, quantidade de partículas, duração e delay.")
    if width % 2 or height % 2:
        raise ValueError("Largura e altura devem ser pares para codificação yuv420p.")
    if not (0 <= bounce <= 1 and 0 <= friction <= 1 and drag >= 0 and gravity >= 0):
        raise ValueError("bounce e friction: 0..1; drag e gravity: >= 0.")
    start, colors = image_particles(input_path, width, height, count, seed)
    floor = height - 1 - particle_size // 2
    particles = explode(start, colors, seed, force, gravity, drag, bounce,
                        friction, width, floor, particle_size // 2)
    frames = round(duration * fps)
    still_frames = round(delay * fps)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
           "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264",
           "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", str(output_path)]
    print(f"Partículas: {len(colors):,} | frames: {frames} | saída: {output_path}", flush=True)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for frame_index in range(frames):
            if frame_index >= still_frames:
                # Substeps reduce tunneling through scene boundaries at high speeds.
                for _ in range(2):
                    particles.step(1 / (fps * 2))
                positions = particles.positions
            else:
                positions = start
            proc.stdin.write(draw_frame(width, height, positions, colors, particle_size))
            if (frame_index + 1) % max(1, fps * 2) == 0:
                print(f"  {frame_index + 1}/{frames} quadros", flush=True)
        proc.stdin.close()
        error = proc.stderr.read().decode("utf-8", errors="replace")
        if proc.wait() != 0:
            raise RuntimeError(f"FFmpeg falhou: {error}")
    except BaseException:
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.close()
        proc.kill()
        proc.wait()
        output_path.unlink(missing_ok=True)
        raise
    finally:
        proc.stderr.close()
    print("Vídeo concluído.", flush=True)
