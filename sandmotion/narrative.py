"""Single continuous 60-second story: sweep, funnel and reconstruction."""
from pathlib import Path
import subprocess
import tempfile
import wave

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from .visuals import draw_particles
from .encoding import encoding_args

BACKGROUND = np.array([12, 14, 23], dtype=np.uint8)


def sweep_order(x: np.ndarray, y: np.ndarray, width: int, seed: int) -> np.ndarray:
    """Organic left-to-right sweep, same function for raster and sampled particles."""
    xn = x / max(width - 1, 1)
    noise = (np.sin(x * .028 + y * .041 + seed * .33) +
             .5 * np.sin(x * .066 - y * .027 + seed * .17)) / 3
    return np.clip(.84 * xn + .16 * (.5 + noise), 0, 1).astype(np.float32)


def funnel_geometry(width: int, height: int):
    circles = ((width*.34, height*.48, width*.045),
               (width*.66, height*.51, width*.045),
               (width*.50, height*.68, width*.050),
               (width*.31, height*.78, width*.035),
               (width*.69, height*.78, width*.035))
    ramps = (((width*.06, height*.55), (width*.40, height*.71)),
             ((width*.94, height*.55), (width*.60, height*.71)))
    return circles, ramps


def _collide(p: np.ndarray, v: np.ndarray, width: int, height: int,
             circles, ramps, dt: float, now: float) -> None:
    # Deterministic lateral current, plus radial scattering on impact.
    v[:, 0] += (75 * np.sin(p[:, 1] * .023 + now * 1.6) +
                35 * np.sin(p[:, 0] * .039 - now * 2.1)) * dt
    for cx, cy, radius in circles:
        delta = p - np.array([cx, cy])
        distance = np.linalg.norm(delta, axis=1)
        hit = distance < radius + 1.5
        if not np.any(hit):
            continue
        normal = delta[hit] / np.maximum(distance[hit, None], 1e-6)
        normal[distance[hit] < 1e-6] = (0, -1)
        p[hit] = np.array([cx, cy]) + normal * (radius + 1.5)
        vn = np.sum(v[hit] * normal, axis=1)
        vh = v[hit]
        vh -= 1.40 * np.minimum(vn, 0)[:, None] * normal
        vh[:, 0] += 85 * normal[:, 0] * dt * 30
        v[hit] = vh
    for a, b in ramps:
        a, b = np.array(a), np.array(b)
        ab = b - a
        t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
        near = a + t[:, None] * ab
        delta = p - near
        dist = np.linalg.norm(delta, axis=1)
        hit = dist < 3
        if not np.any(hit):
            continue
        n = delta[hit] / np.maximum(dist[hit, None], 1e-6)
        n[dist[hit] < 1e-6] = (0, -1)
        p[hit] = near[hit] + 3*n
        vh = v[hit]
        vn = np.sum(vh*n, axis=1)
        vh -= 1.35 * np.minimum(vn, 0)[:, None] * n
        vh[:, 0] += 70 * np.sign(vh[:, 0] + .01) * dt
        v[hit] = vh
    p[:, 0] = np.clip(p[:, 0], 1, width-2)
    p[:, 1] = np.minimum(p[:, 1], height-2)
    bottom = p[:, 1] >= height-2
    v[bottom, 1] = np.minimum(v[bottom, 1], 0) * .20
    v[bottom, 0] *= .96


def narrative_step(p: np.ndarray, v: np.ndarray, origins: np.ndarray,
                   active: np.ndarray, dt: float, now: float, width: int,
                   height: int, circles, ramps) -> None:
    ids = np.flatnonzero(active)
    if not len(ids):
        return
    q = p[ids].copy()
    vel = v[ids].copy()
    if now < 45:
        g = 140 if now < 25 else 210
        vel[:, 1] += g * dt
        vel *= np.exp(-.44 * dt)
        speed = np.linalg.norm(vel, axis=1)
        vel *= np.minimum(1, 370 / np.maximum(speed, 1e-8))[:, None]
        q += vel * dt
        if now >= 25:
            _collide(q, vel, width, height, circles, ramps, dt, now)
        else:
            q[:, 0] = np.clip(q[:, 0], 1, width-2)
            hit = q[:, 1] >= height - 2
            q[hit, 1] = height-2
            vel[hit, 1] *= -.2
            vel[hit, 0] *= .97
    else:
        # Damped homeward spring ramps up smoothly after 45; inverse gravity fades.
        progress = np.clip((now - 45) / 13.0, 0, 1)
        easing = progress * progress * (3 - 2*progress)
        spring = 2.0 + 35.0 * easing
        damping = 2.4 + 11 * easing
        acceleration = spring * (origins[ids] - q) - damping * vel
        acceleration[:, 1] -= 42 * (1 - easing)
        vel += acceleration * dt
        q += vel * dt
        q[:, 0] = np.clip(q[:, 0], 0, width-1)
        q[:, 1] = np.clip(q[:, 1], 0, height-1)
    p[ids] = q
    v[ids] = vel


def draw_narrative(base: np.ndarray, rgb: np.ndarray, alpha: np.ndarray,
                   order: np.ndarray, positions: np.ndarray,
                   colors: np.ndarray, active: np.ndarray, size: int,
                   progress: float, return_blend: float = 0.0) -> bytes:
    # Unreleased artwork remains a dense raster, never randomly sampled.
    visible = (alpha >= 64) & (order > progress)
    frame = base.copy()
    frame[visible] = rgb[visible]
    xy = np.rint(positions[active]).astype(np.int32)
    cc = colors[active]
    h, w = frame.shape[:2]
    for dy in range(-(size//2), size-size//2):
        for dx in range(-(size//2), size-size//2):
            xx, yy = xy[:, 0] + dx, xy[:, 1] + dy
            ok = (xx >= 0) & (xx < w) & (yy >= 0) & (yy < h)
            frame[yy[ok], xx[ok]] = cc[ok]
    if return_blend > 0:
        # Dense reconstruction smoothly removes sampling holes; final frame is exact.
        complete = base.copy()
        complete[alpha > 0] = (base[alpha > 0].astype(np.float32) *
                               (1-alpha[alpha > 0, None]/255.0) +
                               rgb[alpha > 0].astype(np.float32) *
                               (alpha[alpha > 0, None]/255.0)).astype(np.uint8)
        frame = np.rint((1-return_blend)*frame + return_blend*complete).astype(np.uint8)
    return frame.tobytes()


def cue_wave(filename: Path, sample_rate: int = 44100) -> None:
    """Original short synthesized low-frequency drop, placed at 45 s by FFmpeg."""
    t = np.arange(int(.68 * sample_rate), dtype=np.float64) / sample_rate
    phase = 2*np.pi*(125*t - 60*t*t)
    signal = .42*np.sin(phase)*np.exp(-6*t)
    signal += .07 * np.sin(2*np.pi*800*t)*np.exp(-18*t)
    data = (np.clip(signal, -1, 1)*32767).astype('<i2')
    with wave.open(str(filename), 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(sample_rate)
        out.writeframes(data.tobytes())


def add_audio(video: Path, soundtrack: Path | None, cue: bool, duration: float,
              explosion_time: float = 3.0) -> None:
    """Optional user-provided music plus a synthesized cue at precisely 50.0s."""
    if not cue and soundtrack is None:
        return
    # Mux in the destination filesystem: Path.replace() is atomic only there.
    # tempfile's default /tmp may be a different mount (EXDEV on Linux).
    video.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.sandmotion-mux-', dir=video.parent) as td:
        temp = Path(td)
        cue_path = temp/'drop.wav'
        if cue:
            from .soundscape import soundscape_wave
            soundscape_wave(cue_path, duration=duration, explosion_time=explosion_time)
        out = temp/'mux.mp4'
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(video)]
        if soundtrack is not None:
            cmd += ['-stream_loop', '-1', '-i', str(soundtrack)]
        if cue:
            cmd += ['-i', str(cue_path)]
        if soundtrack is not None and cue:
            cmd += ['-filter_complex', '[1:a]volume=0.55[m];[2:a]volume=0.95[c];[m][c]amix=inputs=2:duration=first:normalize=0[a]', '-map','0:v:0','-map','[a]']
        elif cue:
            cmd += ['-map','0:v:0','-map','1:a:0']
        else:
            cmd += ['-map','0:v:0','-map','1:a:0']
        cmd += ['-c:v','copy','-c:a','aac','-b:a','160k', '-t', str(duration), str(out)]
        subprocess.run(cmd, check=True)
        out.replace(video)


def render_narrative(input_path: Path, output_path: Path, *, width: int, height: int,
                     fps: int, duration: float, count: int, seed: int,
                     particle_size: int, crf: int, soundtrack: Path | None = None,
                     drop_sound: bool = True, motion_speed: float = 0.6,
                     encoding_profile: str = "balanced", bitrate_mbps: float | None = None,
                     explosion_time: float = 3.0, **unused) -> None:
    """One long simulation; clean image 0-3s and 57-60s, chaos 3-50s."""
    from .chaos import (DURATION, phase, initial_burst, chaotic_step,
                        rebuild_step, reconstruction_blend)
    from .render import image_particles, load_image
    if not (0.1 <= motion_speed <= 2.0):
        raise ValueError('--motion-speed deve estar entre 0.1 e 2.0')
    video_encoding = encoding_args(encoding_profile, crf=crf, bitrate_mbps=bitrate_mbps)
    if not (0 <= explosion_time < 50):
        raise ValueError('--explosion-time deve ser >= 0 e < 50 segundos')
    if duration != DURATION:
        raise ValueError('O modo narrative exige --duration 60.')
    if width % 2 or height % 2 or min(width, height, fps, count, particle_size) <= 0:
        raise ValueError('Dimensões pares e parâmetros positivos são necessários.')
    if soundtrack is not None and not soundtrack.is_file():
        raise FileNotFoundError(soundtrack)

    original = load_image(input_path, width, height)
    canvas = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    canvas.alpha_composite(original, ((width-original.width)//2,
                                      (height-original.height)//2))
    # A low-contrast blurred version fills otherwise empty vertical space
    # without stretching or cropping the sharp original photo.
    source_rgb = Image.open(input_path).convert('RGB')
    cover = ImageOps.fit(source_rgb, (width, height),
                         method=Image.Resampling.LANCZOS)
    cover = cover.filter(ImageFilter.GaussianBlur(max(8, width//24)))
    cover = ImageEnhance.Brightness(cover).enhance(.22)
    full = cover.convert('RGBA')
    full.alpha_composite(canvas)
    original_rgb = np.asarray(full.convert('RGB'))
    original_bytes = original_rgb.tobytes()
    origins, colors = image_particles(input_path, width, height, count, seed)
    p = origins.copy()
    v = initial_burst(origins, seed, width, height)
    circles, ramps = funnel_geometry(width, height)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo',
           '-pix_fmt','rgb24','-s',f'{width}x{height}','-r',str(fps),
           '-i','-','-an',*video_encoding,
           '-pix_fmt','yuv420p','-movflags','+faststart',
           str(output_path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    total = round(duration*fps)
    try:
        for frame_index in range(total):
            now = frame_index/fps
            scene = phase(now, explosion_time)
            if scene in ('hook', 'hold'):
                data = original_bytes
            else:
                for _ in range(4):
                    dt = 1/(fps*4)
                    if scene == 'chaos':
                        # Slow the physics, not the video clock or the scene boundaries.
                        simulated_time = explosion_time + (now - explosion_time)*motion_speed
                        chaotic_step(p, v, dt*motion_speed, simulated_time,
                                     width, height, circles, ramps)
                    else:
                        rebuild_step(p, v, origins, dt, now)
                frame = np.empty((height, width, 3), dtype=np.uint8)
                frame[:] = BACKGROUND
                draw_particles(frame, p, v, colors, particle_size)
                if scene == 'rebuild':
                    blend = reconstruction_blend(now)
                    if blend:
                        frame = np.rint((1-blend)*frame +
                                        blend*original_rgb).astype(np.uint8)
                data = frame.tobytes()
            proc.stdin.write(data)
            if (frame_index+1) % (max(1, fps*10)) == 0:
                print(f'Narrative: {(frame_index+1)/fps:.0f}/{duration:.0f}s', flush=True)
        proc.stdin.close()
        err = proc.stderr.read().decode('utf-8', 'replace')
        if proc.wait() != 0:
            raise RuntimeError('FFmpeg falhou: '+err)
    except BaseException:
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.close()
        proc.kill()
        proc.wait()
        output_path.unlink(missing_ok=True)
        raise
    finally:
        proc.stderr.close()
    add_audio(output_path, soundtrack, drop_sound, duration,
              explosion_time=explosion_time)
