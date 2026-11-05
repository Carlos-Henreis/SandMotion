# SandMotion v0.3 — Explosão com imagem nítida

Transforma um PNG ou JPEG em partículas explodindo e caindo. O modo padrão **explosion** mostra a imagem original completa (sem amostragem ou pontilhado) antes da explosão. O modo **disintegration** preserva a liberação progressiva.

## Instalação

```bash
sudo apt install ffmpeg python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python examples/make_demo.py
pytest -q
```

## Explosão — vídeo de 60 segundos

```bash
sand-motion imagem.png --output output/explosao.mp4 \
  --mode explosion --duration 60 --cycle-duration 12 \
  --delay 1.5 --particles 60000 --force 1200 \
  --gravity 520 --drag 0.12 --terminal-speed 1400 \
  --bounce 0.25 --friction 0.90 --plinko-rows 0 \
  --fps 30
```

**Timeline:** cinco ciclos de 12 segundos no MP4 de 60 segundos. Em cada ciclo: imagem original limpa por 1,5 s, explosão radial instantânea e queda durante os 10,5 s seguintes. A imagem reaparece no começo de cada ciclo (corte intencional). Não é uma única explosão sustentada fisicamente por 60 s.

O modo `explosion` é o padrão. Para vídeo curto, use `--duration 12`, mantendo `--cycle-duration 12`.

## Desintegração gradual (alternativa)

```bash
sand-motion imagem.png --mode disintegration --duration 60 \
  --delay 2 --release-duration 48 --release-mode bottom-up \
  --force 230 --gravity 150 --drag 0.52 \
  --terminal-speed 210 --plinko-rows 4
```

## Parâmetros

- `--mode explosion|disintegration`: comportamento do motor
- `--duration`: duração final do MP4 (padrão: 60 s)
- `--cycle-duration`: duração de cada ciclo explosivo (padrão: 12 s)
- `--delay`: tempo com imagem raster nítida antes de cada explosão
- `--particles`: limite de partículas após a explosão; não limita os pixels da prévia
- `--force`, `--gravity`, `--drag`, `--terminal-speed`: parâmetros físicos
- `--plinko-rows`: 0 desativa obstáculos invisíveis (padrão no modo explosion)
- `--release-duration` e `--release-mode`: apenas modo disintegration

## Limitações

As partículas são independentes, sem colisão entre elas. Durante a explosão podem existir espaços visíveis entre grãos — isso não afeta a nitidez da imagem inicial. O vídeo não contém áudio. A renderização usa FFmpeg.
