# SandMotion v0.4 — Narrative (60 segundos)

Gera um vídeo de 60 segundos a partir de PNG/JPEG, com **uma única simulação contínua**: imagem nítida → desintegração esquerda-direita → funil com turbulência → reconstrução fiel à imagem original. Sem reinícios a cada 12 segundos.

## Instalação no Debian

```bash
sudo apt install ffmpeg python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest -q
python examples/make_demo.py
```

## Gerar vídeo de 60 segundos (modo padrão)

```bash
sand-motion imagem.png --output output/narrative.mp4 --mode narrative \
  --duration 60 --width 540 --height 960 --fps 30 --particles 60000
```

Com trilha fornecida por você:

```bash
sand-motion imagem.png --mode narrative --soundtrack minha-trilha.mp3 \
  --output output/com-musica.mp4
```

O motor adiciona **um efeito de drop sintetizado** no segundo **45.000**. Se fornecer sua própria trilha, ela será combinada com esse efeito. Para desativar o efeito, use `--no-drop-sound`. Não há seleção automática de batidas musicais nem alteração inteligente do arranjo; o marcador sonoro fica rigorosamente nos 45 segundos.

### Timeline

| Tempo | Cena |
| --- | --- |
| 0–5 s | Imagem original raster intacta |
| 5–25 s | Liberação orgânica da esquerda para a direita, com ruído espacial |
| 25–45 s | 5 círculos e 2 rampas invisíveis com turbulência lateral |
| 45–58 s | Atração amortecida crescente para as posições originais |
| 58–60 s | Transição suave para a imagem raster completa; último quadro coincide com a imagem inicial |

O modo usa pixels completos na parte da imagem ainda não liberada, evitando o efeito pontilhado visto na v0.2. A fase de retorno preserva as posições originais de cada partícula; a composição raster final corrige os intervalos entre partículas amostradas.

**Observação:** nas fases 5–45s, as partículas são independentes e ainda podem se sobrepor, sem colisão grão-grão. O formato final é MP4 H.264 + AAC (quando há efeito de áudio ou trilha).

## Outros modos preservados

```bash
# Explosões radiais repetidas, para vídeos curtos
sand-motion imagem.png --mode explosion --duration 12 --cycle-duration 12

# Desintegração progressiva antiga
sand-motion imagem.png --mode disintegration --duration 60 \
  --delay 2 --release-duration 48 --release-mode bottom-up
```

## Notas de desempenho

Comece em 540x960, 30 FPS com 20–60 mil partículas; 1080x1920 a 60 FPS é significativamente mais caro. O modo narrative exige `--duration 60` porque os marcos de tempo são absolutos. Os modos anteriores continuam disponíveis.
