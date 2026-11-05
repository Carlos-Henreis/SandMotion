# SandMotion v0.7 — Explosão mais lenta e som sincronizado

Renderizador em Python de um vídeo único de 60 segundos, com explosão, física de partículas, retorno e sons originais sintetizados automaticamente.

## Instalação

```bash
sudo apt install ffmpeg python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest -q
```

## Exportação compacta (novo padrão)

O perfil `social` gera H.264 com `libx264 -preset slow -b:v 4M -maxrate 5M -bufsize 10M`. O objetivo é reduzir bastante o tamanho **sem precisar recodificar o MP4 depois**. O bitrate médio é um alvo, e o tamanho exato depende do conteúdo.

| Perfil | Configuração |
| --- | --- |
| `social` (padrão) | 4 Mb/s, pico 5 Mb/s |
| `balanced` | 6 Mb/s, pico 7,5 Mb/s |
| `quality` | CRF 20, sem alvo de tamanho |

O limite de bitrate não implica um tamanho máximo rigoroso. Para personalizar:

```bash
sand-motion image.png --mode narrative --encoding-profile social \\
  --bitrate-mbps 3 --output output/narrative.mp4
```

Para priorizar qualidade, use `--encoding-profile quality --crf 20`. Esses perfis também funcionam nos modos `explosion` e `disintegration`.

## Parametrizar o instante da explosão

Use `--explosion-time` para escolher quantos segundos a imagem permanece intacta antes da explosão. O padrão é **3 segundos**. São aceitos valores de 0 até menos de 50 segundos; o retorno continua começando no segundo 50 e a imagem final reaparece aos 57. O som da explosão e o início do som das partículas acompanham a configuração.

```bash
sand-motion image.png --mode narrative --explosion-time 6 \
  --motion-speed 0.5 --output output/narrative.mp4
```

## Criar seu vídeo

```bash
sand-motion image.png --mode narrative --output output/narrative.mp4 \
  --duration 60 --width 540 --height 960 --fps 30 \
  --particles 60000 --motion-speed 0.6
```

### Controlar a velocidade

`--motion-speed` altera somente a **simulação das partículas durante o caos**, não o FPS nem os marcos de tempo (0–3, 3–50, 50–57, 57–60).

| Valor | Movimento |
| --- | --- |
| 0.3 | Bem lento |
| 0.5 | Lento |
| 0.6 | Padrão (mais lento que v0.5) |
| 1.0 | Velocidade original da v0.5 |
| 1.5 | Rápido |

Faixa válida: 0.1 a 2.0. Velocidades pequenas produzem trajetórias mais curtas e menos colisões com os obstáculos.

### Sons sintetizados automaticamente

- **3s:** impacto explosivo e ruído de dispersão;
- **3–50s:** textura de movimento / vento granular, modulada continuamente;
- **50–57s:** som ascendente de retorno e reconstrução;
- **57s:** breve sinal tonal de conclusão.

Não exige arquivo de áudio externo. Para incluir música própria:

```bash
sand-motion image.png --mode narrative --motion-speed 0.5 \
  --soundtrack minha-musica.mp3 --output output/com-musica.mp4
```

A música é misturada à camada de efeitos. Use `--no-drop-sound` para desativar **toda a trilha de efeitos sintetizados**; caso forneça `--soundtrack`, a música continua.

O arquivo temporário de áudio é montado no diretório do vídeo final para evitar erro `Invalid cross-device link`.

## Timeline

| Tempo | Imagem |
| --- | --- |
| 0–3 s | Imagem inteira e nítida |
| 3–50 s | Explosão e vórtices contínuos com obstáculos invisíveis |
| 50–57 s | Reconstrução amortecida e retorno ao raster original |
| 57–60 s | Imagem final intacta |

## Outros modos

```bash
sand-motion image.png --mode explosion --duration 12 --cycle-duration 12
sand-motion image.png --mode disintegration --duration 60 --delay 2 --release-duration 48
```

`--motion-speed` só altera o modo `narrative`. O áudio é sintetizado a partir de sinais originais; não inclui música comercial.
