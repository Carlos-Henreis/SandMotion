import argparse
from pathlib import Path
from .render import render


def main():
    parser = argparse.ArgumentParser(description="SandMotion — explosões ou desintegração progressiva em vídeo.")
    parser.add_argument("image", type=Path, help="PNG/JPEG de entrada")
    parser.add_argument("--output", type=Path, default=Path("output.mp4"))
    parser.add_argument("--soundtrack", type=Path, default=None, help="Trilha opcional misturada aos efeitos de explosão, movimento e retorno")
    parser.add_argument("--no-drop-sound", dest="drop_sound", action="store_false", help="Desativa os sons sintetizados de explosão, movimento e retorno")
    parser.set_defaults(drop_sound=True)
    parser.add_argument("--width", type=int, default=720)
    parser.add_argument("--height", type=int, default=1280)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--explosion-time", type=float, default=3.0,
                        help="Segundo da explosão no modo narrative (0 <= tempo < 50; padrão 3)")
    parser.add_argument("--motion-speed", type=float, default=0.6,
                        help="Velocidade física das partículas no narrative (0.1 a 2.0; padrão 0.6)")
    parser.add_argument("--duration", type=float, default=60)
    parser.add_argument("--mode", choices=("narrative", "explosion", "disintegration"), default="narrative")
    parser.add_argument("--cycle-duration", type=float, default=12,
                        help="Intervalo entre explosões no modo explosion")
    parser.add_argument("--delay", type=float, default=1.5, help="Imagem intacta em segundos")
    parser.add_argument("--release-duration", type=float, default=48,
                        help="Tempo durante o qual partículas são liberadas")
    parser.add_argument("--release-mode", choices=("bottom-up", "noise"), default="bottom-up")
    parser.add_argument("--particles", type=int, default=90000, dest="count")
    parser.add_argument("--force", type=float, default=1200)
    parser.add_argument("--gravity", type=float, default=520)
    parser.add_argument("--drag", type=float, default=0.12)
    parser.add_argument("--terminal-speed", type=float, default=1400)
    parser.add_argument("--bounce", type=float, default=0.25)
    parser.add_argument("--friction", type=float, default=0.90)
    parser.add_argument("--plinko-rows", type=int, default=0,
                        help="Linhas de obstáculos circulares invisíveis; 0 desliga")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--particle-size", type=int, default=3)
    parser.add_argument("--encoding-profile", choices=("social", "balanced", "quality"),
                        default="balanced", help="social: 4 Mb/s, balanced: 6 Mb/s, quality: CRF")
    parser.add_argument("--bitrate-mbps", type=float, default=None,
                        help="Define bitrate médio de vídeo em Mb/s (sobrescreve social/balanced)")
    parser.add_argument("--crf", type=int, default=20,
                        help="Qualidade CRF usada no perfil quality; 0-51")
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error(f"Imagem inexistente: {args.image}")
    render(args.image, args.output,
           **{k: v for k, v in vars(args).items() if k not in ("image", "output")})


if __name__ == "__main__":
    main()
