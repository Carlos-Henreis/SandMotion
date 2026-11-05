# SandMotion v0.2 — Particle Explosion (60 segundos)

Renderizador procedural em Python: uma imagem PNG/JPEG se desintegra progressivamente em milhares de partículas, que explodem, caem lentamente e desviam de obstáculos circulares invisíveis (Plinko).

## Instalação no Debian

```bash
sudo apt install ffmpeg python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python examples/make_demo.py
```

## Vídeo padrão de 60 segundos

```bash
sand-motion examples/demo.png --output output/demo.mp4
```

O preset padrão gera **60 s, 540×960, 30 FPS**:
- 0–2 s: imagem estática
- 2–50 s: desintegração progressiva de baixo para cima, com ruído espacial
- 50–60 s: partículas restantes continuam sob gravidade e batem no chão/obstáculos

```bash
sand-motion minha-imagem.png --output output/viral.mp4 \
  --duration 60 --delay 2 --release-duration 48 \
  --release-mode bottom-up --plinko-rows 4 \
  --gravity 150 --drag 0.52 --terminal-speed 210 \
  --force 230 --fps 30 --particles 30000
```

## Parâmetros relevantes

| Flag | Padrão | Significado |
| --- | --- | --- |
| `--duration` | 60 | Duração total em segundos |
| `--delay` | 2 | Imagem intacta antes da primeira desintegração |
| `--release-duration` | 48 | Janela de liberação gradual de partículas |
| `--release-mode` | bottom-up | `bottom-up` ou `noise` |
| `--gravity` | 150 | Gravidade em pixels/s² |
| `--drag` | 0.52 | Resistência exponencial do ar |
| `--terminal-speed` | 210 | Velocidade máxima em pixels/s |
| `--plinko-rows` | 4 | Fileiras de círculos invisíveis; 0 desativa |
| `--force` | 230 | Força de explosão em pixels/s |
| `--particles` | 30000 | Quantidade máxima de partículas |
| `--seed` | 42 | Sequência reproduzível |

Use `--width 1080 --height 1920 --fps 60` para Full HD vertical; a renderização será mais lenta.

## Testes

```bash
pip install -e '.[test]'
pytest -q
```

## Limitações

- Colisão com o piso, paredes e círculos invisíveis, mas **sem colisões entre partículas**.
- Obstáculos geométricos fixos, com resposta de contato aproximada.
- Exportação MP4/H.264 sem áudio.
- A desintegração gradual preserva a imagem até a liberação de cada partícula; é uma programação de ativação, não uma simulação de material granular contínuo.
