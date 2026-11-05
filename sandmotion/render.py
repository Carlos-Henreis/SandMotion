"""Render clean source frames before particle explosions or gradual disintegration."""
import shutil
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from .physics import explode, plinko_obstacles, release_times
from .encoding import encoding_args


def load_image(path: Path, width: int, height: int) -> Image.Image:
    rgba = Image.open(path).convert("RGBA")
    rgba.thumbnail((int(width * 0.75), int(height * 0.54)), Image.Resampling.LANCZOS)
    return rgba


def load_centered_rgb(path: Path, width: int, height: int,
                      background=(12, 14, 23)) -> np.ndarray:
    """Render complete, un-sampled pixels (including composited transparency)."""
    rgba = load_image(path, width, height)
    canvas = Image.new("RGBA", (width, height), (*background, 255))
    canvas.alpha_composite(rgba, ((width - rgba.width) // 2,
                                  (height - rgba.height) // 2))
    return np.asarray(canvas.convert("RGB"))


def image_particles(path: Path, width: int, height: int, max_particles: int,
                    seed: int) -> tuple[np.ndarray, np.ndarray]:
    rgba = load_image(path, width, height)
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
    for dy in range(-(size // 2), size - size // 2):
        for dx in range(-(size // 2), size - size // 2):
            x = coords[:, 0] + dx
            y = coords[:, 1] + dy
            valid = (x >= 0) & (x < width) & (y >= 0) & (y < height)
            frame[y[valid], x[valid]] = colors[valid]
    return frame.tobytes()


def render(input_path: Path, output_path: Path, *, width: int = 540,
           height: int = 960, fps: int = 30, duration: float = 60.0,
           delay: float = 1.5, release_duration: float = 48.0,
           release_mode: str = "bottom-up", mode: str = "narrative",
           cycle_duration: float = 12.0, count: int = 60000,
           force: float = 1200.0, gravity: float = 520.0, drag: float = 0.12,
           bounce: float = 0.25, friction: float = 0.90, terminal_speed: float = 1400.0,
           plinko_rows: int = 0, seed: int = 42, particle_size: int = 2,
           crf: int = 20, soundtrack: Path | None = None,
           drop_sound: bool = True, motion_speed: float = 0.6,
           encoding_profile: str = "social", bitrate_mbps: float | None = None) -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg não encontrado. Instale com: sudo apt install ffmpeg")
    if mode == "narrative":
        from .narrative import render_narrative
        return render_narrative(input_path, output_path, width=width, height=height,
                                fps=fps, duration=duration, count=count, seed=seed,
                                particle_size=particle_size, crf=crf,
                                soundtrack=soundtrack, drop_sound=drop_sound,
                                motion_speed=motion_speed,
                                encoding_profile=encoding_profile, bitrate_mbps=bitrate_mbps)
    if soundtrack is not None:
        raise ValueError("--soundtrack é suportado no modo narrative.")
    video_encoding = encoding_args(encoding_profile, crf=crf, bitrate_mbps=bitrate_mbps)
    if min(width, height, fps, count, particle_size) <= 0 or duration <= 0:
        raise ValueError("Resolução, FPS, duração, partículas e tamanho devem ser positivos.")
    if mode not in ("explosion", "disintegration"):
        raise ValueError("mode deve ser explosion ou disintegration.")
    if delay < 0 or release_duration <= 0 or cycle_duration <= delay:
        raise ValueError("Exige delay >= 0, release_duration > 0 e cycle_duration > delay.")
    if mode == "disintegration" and delay + release_duration > duration:
        raise ValueError("delay + release_duration deve caber na duração total.")
    if width % 2 or height % 2:
        raise ValueError("Largura e altura devem ser pares para yuv420p.")
    if not (0 <= bounce <= 1 and 0 <= friction <= 1 and drag >= 0 and gravity >= 0
            and terminal_speed > 0 and force >= 0 and plinko_rows >= 0):
        raise ValueError("Valores físicos inválidos.")
    raster_frame = load_centered_rgb(input_path, width, height).tobytes()
    start, colors = image_particles(input_path, width, height, count, seed)
    floor = height - 1 - particle_size // 2
    obstacles = plinko_obstacles(width, height, plinko_rows)
    def new_system():
        return explode(start, colors, seed, force, gravity, drag, bounce,
                       friction, width, floor, particle_size // 2,
                       terminal_speed, obstacles)

    particles = new_system()
    schedule = (release_times(start, seed, release_duration, release_mode) + delay
                if mode == "disintegration" else None)
    frames = round(duration * fps)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
           "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264",
           *video_encoding, "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", str(output_path)]
    print(f"Modo: {mode} | Partículas: {len(colors):,} | duração: {duration}s | "
          f"ciclo: {cycle_duration}s | obstáculos: {len(obstacles)}", flush=True)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        cycle_frames = max(1, round(cycle_duration * fps))
        still_frames = round(delay * fps)
        for frame_index in range(frames):
            if mode == "explosion":
                cycle_frame = frame_index % cycle_frames
                if cycle_frame == 0 and frame_index != 0:
                    particles = new_system()
                if cycle_frame < still_frames:
                    frame_bytes = raster_frame
                else:
                    for _ in range(4):
                        particles.step(1 / (fps * 4))
                    frame_bytes = draw_frame(width, height, particles.positions,
                                             colors, particle_size)
            else:
                time = frame_index / fps
                active = time >= schedule
                if np.any(active):
                    for _ in range(4):
                        particles.step(1 / (fps * 4), active)
                frame_bytes = (raster_frame if time < delay
                               else draw_frame(width, height, particles.positions,
                                               colors, particle_size))
            proc.stdin.write(frame_bytes)
            if (frame_index + 1) % max(1, fps * 5) == 0:
                print(f"  {frame_index + 1}/{frames} frames", flush=True)
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
