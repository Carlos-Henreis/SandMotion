"""FFmpeg H.264 encoding profiles shared by all SandMotion render modes.

Social uses an average bitrate target plus VBV peak control, avoiding large
CRF-only outputs for high-entropy particle scenes. File size is approximate,
not an exact upper bound.
"""

PROFILES = ("social", "balanced", "quality")


def encoding_args(profile: str = "social", *, crf: int = 20,
                  bitrate_mbps: float | None = None) -> list[str]:
    if profile not in PROFILES:
        raise ValueError(f"Perfil inválido: {profile}; escolha entre {', '.join(PROFILES)}")
    if not (0 <= crf <= 51):
        raise ValueError("--crf deve estar entre 0 e 51")
    if bitrate_mbps is not None and not (0.1 <= bitrate_mbps <= 100):
        raise ValueError("--bitrate-mbps deve estar entre 0.1 e 100")
    args = ["-c:v", "libx264", "-preset", "slow"]
    if profile == "quality" and bitrate_mbps is None:
        args += ["-crf", str(crf)]
    else:
        target = bitrate_mbps if bitrate_mbps is not None else (
            4.0 if profile == "social" else 6.0)
        peak = target * 1.25
        buffer = target * 2.5
        args += ["-b:v", f"{target:g}M", "-maxrate", f"{peak:g}M",
                 "-bufsize", f"{buffer:g}M"]
    return args
