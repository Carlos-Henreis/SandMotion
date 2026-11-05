# SandMotion v0.5 — Explosão contínua de 60 segundos

Uma única simulação procedural em Python: imagem completa, explosão radial forte, partículas em movimento frenético por toda a tela e reconstrução da imagem. Sem repetições de ciclos e sem partículas paradas no rodapé.

## Timeline do modo narrative (padrão)

| Intervalo | Cena |
| --- | --- |
| 0–3 s | Imagem original, renderizada integralmente (sem pontilhado) |
| 3–50 s | Explosão radial e caos contínuo com vórtices, correntes, círculos e rampas invisíveis |
| 50–57 s | Retorno amortecido às posições originais e blend gradual do raster |
| 57–60 s | Imagem original intacta para encerrar e fechar o loop |

O efeito sonoro sintetizado de transição foi deslocado do segundo 45 para o segundo **50**, junto com a reconstrução.

## Instalação e execução

```bash
sudo apt install ffmpeg python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest -q

sand-motion image.png --mode narrative --output output/narrative.mp4 \
  --duration 60 --width 540 --height 960 --fps 30 --particles 60000
```

Para incluir uma trilha própria (repetida caso seja mais curta):

```bash
sand-motion image.png --mode narrative --soundtrack musica.mp3 \
  --output output/com-trilha.mp4
```

Use `--no-drop-sound` para desabilitar o efeito sintetizado no momento da reconstrução.

## Modos anteriores (preservados)

```bash
sand-motion image.png --mode explosion --duration 12 --cycle-duration 12
sand-motion image.png --mode disintegration --duration 60 \
  --delay 2 --release-duration 48 --release-mode bottom-up
```

## Observações

- A explosão e a turbulência usam partículas independentes, não colisões grão-grão.
- A simulação não gera uma imagem rasterizada completa durante a explosão: fragmentos podem ficar separados, mas o original no início e no fim sempre mantém sua qualidade.
- Física com integração em passos fixos, vórtices e limites com rebote; pode ser ajustada depois para outros efeitos.
- A duração de `narrative` é fixa em 60 segundos. Exportação MP4 H.264, áudio AAC quando ativado.
