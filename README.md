# SandMotion 0.1.0 — Particle Explosion

Gera vídeos MP4 com explosão radial de partículas coloridas extraídas de imagens PNG/JPEG, seguida de gravidade e colisão com chão e paredes.

## Instalação (Debian/Linux)

```bash
sudo apt install ffmpeg python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Rodar o exemplo

Primeiro, gere uma imagem de demonstração:

```bash
python examples/make_demo.py
sand-motion examples/demo.png --output output/demo.mp4 \
  --duration 8 --delay 1 --fps 30 --particles 30000
```

Ou, sem usar o comando instalado:

```bash
python -m sandmotion examples/demo.png --output output/demo.mp4
```

## Criar vídeo vertical em Full HD

```bash
sand-motion sua-imagem.png --output output/viral.mp4 \
  --width 1080 --height 1920 --fps 60 \
  --duration 12 --delay 2 --particles 80000 \
  --force 850 --gravity 1050 --particle-size 2 --seed 42
```

Para PNG transparente, apenas pixels com alpha >= 64 viram partículas. Imagens opacas incluem o fundo. A imagem é redimensionada para caber na região central e preserva as cores.

## Parâmetros

| Flag | Padrão | Efeito |
| --- | --- | --- |
| `--force` | 650 | Potência da explosão (pixels/s) |
| `--gravity` | 900 | Gravidade (pixels/s²) |
| `--drag` | 0.22 | Arrasto exponencial (1/s) |
| `--bounce` | 0.35 | Restituição em choques (0–1) |
| `--friction` | 0.74 | Retenção da velocidade horizontal no chão (0–1) |
| `--particles` | 30000 | Máximo de partículas amostradas |
| `--particle-size` | 2 | Tamanho quadrado da partícula renderizada |
| `--seed` | 42 | Reprodutibilidade |
| `--delay` | 1 | Tempo inicial com a imagem estática |

## Testes

```bash
pip install -e '.[test]'
pytest -q
```

## Limitações da v0.1

- Simulação vetorizada NumPy, integração semi-implícita.
- Colisões apenas com piso e paredes; ainda sem colisões entre partículas.
- Sprites quadrados podem se sobrepor; não formam pilhas físicas.
- Exportação offline em H.264 com FFmpeg.
- Sem áudio, máscara progressiva, obstáculos ou GPU.
