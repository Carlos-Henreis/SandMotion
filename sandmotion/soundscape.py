"""Original procedural sound design synchronized to the narrative timeline.

No external music or copyright-restricted samples are used. The 60s mono
soundscape combines an impact at 3s, swirling granular ambience and a reverse
sweep at 50s. Deterministic seed and bounded synthesis levels.
"""
from pathlib import Path
import wave
import numpy as np

SAMPLE_RATE = 24000


def soundscape(duration: float = 60., seed: int = 42, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    if duration <= 0 or sample_rate <= 0:
        raise ValueError("duration and sample_rate must be positive")
    rng = np.random.default_rng(seed)
    length = round(duration * sample_rate)
    out = np.zeros(length, dtype=np.float32)

    def add_at(time: float, signal: np.ndarray) -> None:
        first = round(time * sample_rate)
        if first >= length:
            return
        if first < 0:
            signal = signal[-first:]
            first = 0
        samples = min(len(signal), length-first)
        if samples:
            out[first:first+samples] += signal[:samples]

    # 3 seconds: burst with deep punch and airy sharp transient.
    n = round(2.5*sample_rate)
    t = np.arange(n, dtype=np.float32)/sample_rate
    phase = 2*np.pi*(160*t - 52*t*t)
    bass = .55*np.sin(phase)*np.exp(-4.5*t)
    burst_noise = rng.standard_normal(n).astype(np.float32)
    # Differencing creates a brighter crash without a DSP dependency.
    bright = burst_noise - np.roll(burst_noise, 1)
    explosion = bass + .12*bright*np.exp(-7*t)
    add_at(3., explosion)

    # 3-50 seconds: long evolving airflow / fine-grain rustle.
    lo = round(3*sample_rate)
    hi = min(round(50*sample_rate), length)
    if hi > lo:
        count = hi-lo
        tt = np.arange(count, dtype=np.float32)/sample_rate
        noise = rng.standard_normal(count).astype(np.float32)
        # Smooth moving-average band emphasis; avoids shrill white-noise bed.
        filtered = np.cumsum(noise, dtype=np.float64)
        window = max(4, sample_rate//700)
        smoothed = (filtered[window:] - filtered[:-window])/window
        rough = np.zeros(count, dtype=np.float32)
        rough[window:] = smoothed.astype(np.float32)
        modulation = .55 + .45*np.sin(2*np.pi*(.23*tt + .002*tt*tt))**2
        fadein = np.clip(tt/.45, 0, 1)
        fadeout = np.clip((47-tt)/.8, 0, 1)
        out[lo:hi] += .12*rough*modulation*fadein*fadeout

    # 50 seconds: reverse / gathering sweep converging into a tonal landing.
    n = round(7*sample_rate)
    t = np.arange(n, dtype=np.float32)/sample_rate
    freq = 105 + 470*(t/7)**1.4
    phase = 2*np.pi*np.cumsum(freq, dtype=np.float64)/sample_rate
    envelope = (np.clip(t/.7, 0, 1) *
                np.clip((7-t)/1.3, 0, 1))
    reverse = .23*np.sin(phase).astype(np.float32)*envelope
    reverse += .12*np.sin(2*phase).astype(np.float32)*envelope
    add_at(50., reverse)

    # Soft confirmation at 57s when original image returns.
    n = round(1.8*sample_rate)
    t = np.arange(n, dtype=np.float32)/sample_rate
    bell = (.15*np.sin(2*np.pi*660*t) + .08*np.sin(2*np.pi*990*t))
    add_at(57., bell.astype(np.float32)*(1-np.exp(-25*t))*np.exp(-3.3*t))
    return np.clip(out, -.95, .95)


def soundscape_wave(path: Path, duration: float = 60., seed: int = 42,
                    sample_rate: int = SAMPLE_RATE) -> None:
    audio = soundscape(duration, seed, sample_rate)
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes((audio*32767).astype('<i2').tobytes())
