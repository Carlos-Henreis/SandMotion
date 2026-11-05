import argparse
from pathlib import Path
from .render import render


def main():
    parser = argparse.ArgumentParser(description="SandMotion — explosões ou desintegração progressiva em vídeo.")
    parser.add_argument("image", type=Path, help="PNG/JPEG de entrada")
    parser.add_argument("--output", type=Path, default=Path("output.mp4"))
    parser.add_argument("--soundtrack", type=Path, default=None, help="Trilha sonora própria opcional, sincronizada com o efeito aos 45s")
    parser.add_argument("--no-drop-sound", dest="drop_sound", action="store_false", help="Desativa o efeito sonoro sintetizado aos 45s")
    parser.set_defaults(drop_sound=True)
    parser.add_argument("--width", type=int, default=540)
    parser.add_argument("--height", type=int, default=960)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--duration", type=float, default=60)
    parser.add_argument("--mode", choices=("narrative", "explosion", "disintegration"), default="narrative")
    parser.add_argument("--cycle-duration", type=float, default=12,
                        help="Intervalo entre explosões no modo explosion")
    parser.add_argument("--delay", type=float, default=1.5, help="Imagem intacta em segundos")
    parser.add_argument("--release-duration", type=float, default=48,
                        help="Tempo durante o qual partículas são liberadas")
    parser.add_argument("--release-mode", choices=("bottom-up", "noise"), default="bottom-up")
    parser.add_argument("--particles", type=int, default=60000, dest="count")
    parser.add_argument("--force", type=float, default=1200)
    parser.add_argument("--gravity", type=float, default=520)
    parser.add_argument("--drag", type=float, default=0.12)
    parser.add_argument("--terminal-speed", type=float, default=1400)
    parser.add_argument("--bounce", type=float, default=0.25)
    parser.add_argument("--friction", type=float, default=0.90)
    parser.add_argument("--plinko-rows", type=int, default=0,
                        help="Linhas de obstáculos circulares invisíveis; 0 desliga")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--particle-size", type=int, default=2)
    parser.add_argument("--crf", type=int, default=20)
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error(f"Imagem inexistente: {args.image}")
    render(args.image, args.output,
           **{k: v for k, v in vars(args).items() if k not in ("image", "output")})


if __name__ == "__main__":
    main()
