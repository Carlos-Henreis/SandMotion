import argparse
from pathlib import Path
from .render import render


def main():
    parser = argparse.ArgumentParser(description="SandMotion — exploda qualquer PNG em partículas coloridas.")
    parser.add_argument("image", type=Path, help="PNG/JPEG com imagem de entrada")
    parser.add_argument("--output", type=Path, default=Path("output.mp4"))
    parser.add_argument("--width", type=int, default=540)
    parser.add_argument("--height", type=int, default=960)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--duration", type=float, default=8)
    parser.add_argument("--delay", type=float, default=1.0, help="Segundos de imagem intacta")
    parser.add_argument("--particles", type=int, default=30000, dest="count")
    parser.add_argument("--force", type=float, default=650)
    parser.add_argument("--gravity", type=float, default=900)
    parser.add_argument("--drag", type=float, default=0.22)
    parser.add_argument("--bounce", type=float, default=0.35)
    parser.add_argument("--friction", type=float, default=0.74)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--particle-size", type=int, default=2)
    parser.add_argument("--crf", type=int, default=20)
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error(f"Imagem inexistente: {args.image}")
    render(args.image, args.output, **{k: v for k, v in vars(args).items() if k not in ("image", "output")})


if __name__ == "__main__":
    main()
