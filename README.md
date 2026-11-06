# 🎬 Agente de Vídeos Virais com Mascote & Lip Sync

> **Pipeline profissional para criar vídeos verticais (Reels, TikTok, Shorts) 1080x1920 a 30 fps com mascote falante, sincronização labial fonética (Rhubarb), voz humana contínua (Fish Audio, ElevenLabs ou VoiceStudio local), legendas palavra a palavra e renderização determinística via HyperFrames.**

---

## ⚡ O que este agente faz

Transforma uma ideia ou vídeo viral de referência em um **vídeo vertical pronto para postar** com o seu próprio mascote ilustrado:
- **9 Poses Expressivas:** Geradas via Nano Banana com fundo liso e consistência de personagem.
- **Voz 100% Humana e Fluida:** Síntese contínua em chamada única (sem pausas robóticas entre frases) via Fish Audio, ElevenLabs ou VoiceStudio local (grátis).
- **Lip Sync Fonético com Rhubarb:** Mapeamento de 9 formas de boca vetoriais (A a H + X repouso) que acompanham cada fonema do português.
- **Boca Fecha no Silêncio:** Algoritmo que detecta pausas de áudio e garante zero bocas abertas no silêncio.
- **Legendas Dinâmicas:** Sincronizadas palavra por palavra, com destaque de cor e zoom de câmera na ênfase (`*palavra*`).
- **Render Determinístico via HyperFrames:** HTML5 + GSAP compilado diretamente em MP4 1080x1920 30 fps sem editor de vídeo pesado.

---

## 📐 Pipeline

```
  ┌─────────────────┐       ┌──────────────────────┐       ┌────────────────────┐
  │   Nano Banana   │  ──▶  │  Recorte & Marcação  │  ──▶  │  Síntese de Voz   │
  │ (9 poses limpas)│       │ (recorta.py/rosto.py)│       │ (vozes.py TTS)     │
  └─────────────────┘       └──────────────────────┘       └────────────────────┘
                                                                     │
  ┌─────────────────┐       ┌──────────────────────┐                 │
  │   Vídeo Final   │  ◀──  │     HyperFrames      │  ◀──────────────┘
  │  (saida/*.mp4)  │       │ (HTML + GSAP render) │   (Rhubarb Lip Sync)
  └─────────────────┘       └──────────────────────┘
```

---

## 📂 Estrutura do Repositório

```
agente-videos-mascote-lipsync/
├── SKILL.md            # Documentação completa e instrução para agentes de IA
├── README.md           # Guia de início rápido e visão geral
├── requirements.txt    # Dependências Python
├── scripts/
│   ├── recorta.py      # Remove fundo e calcula transparência
│   ├── rosto.py        # Grade de medição, base sem boca e folha de conferência
│   ├── mascote_rig.py  # Stage SVG com 9 bocas vetoriais, pálpebras e respiração
│   ├── vozes.py        # Wrapper unificado para Fish Audio, ElevenLabs e VoiceStudio
│   └── video.py        # Pipeline de montagem, timeline GSAP e render MP4
└── mascote/            # Diretório de trabalho do personagem (criado no uso)
    ├── src/            # As 9 imagens do Nano Banana
    ├── poses/          # Recortes transparentes e bases sem boca
    ├── layout.json     # Coordenadas de boca e olhos de cada pose
    └── config.json     # Provedor de voz, cores e parâmetros
```

---

## 🚀 Instalação & Pré-requisitos

### 1. Dependências do Sistema

- **Python 3.10+**
- **Node.js 20+**
- **FFmpeg & FFprobe**
- **Rhubarb Lip Sync** (versão 1.13+)

#### Linux / WSL / Ubuntu:
```bash
sudo apt-get update && sudo apt-get install -y ffmpeg libboost-dev cmake build-essential
git clone --depth 1 https://github.com/DanielSWolf/rhubarb-lip-sync ~/repos/rhubarb-lip-sync
cd ~/repos/rhubarb-lip-sync && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc) rhubarb
export RHUBARB=$HOME/repos/rhubarb-lip-sync/build/rhubarb/rhubarb
```

#### Windows:
- Baixe o release do [Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync/releases) (`rhubarb.exe`) e coloque no PATH ou defina a variável `RHUBARB=C:\caminho\rhubarb.exe`.
- Instale o FFmpeg via `winget install Gyan.FFmpeg` ou baixe pelo site oficial.

### 2. Dependências Node.js & Python

```bash
# Dependências Python
pip install -r requirements.txt

# Renderizador HyperFrames & Playwright
npm install -g hyperframes
npx playwright install chromium
```

---

## 🎙️ Provedores de Voz Suportados

Configure em `mascote/config.json`:

| Provedor | Modo | Variável de Ambiente | Destaque |
|---|---|---|---|
| **Fish Audio** | API Nuvem | `export FISH_API_KEY="..."` | PT-BR natural, Voice Design e clonagem rápida |
| **ElevenLabs** | API Nuvem | `export ELEVENLABS_API_KEY="..."` | Máxima expressividade e timestamps por palavra |
| **VoiceStudio** | Local / API | `export VOICESTUDIO_URL="http://127.0.0.1:3900"` | 100% gratuito, sem limite de uso e offline |

---

## 🛠️ Passo a Passo Rápido

### Passo 1: 9 Poses no Nano Banana
Gere o mascote em 9 poses com fundo liso monocromático (ex.: `#BFE3FF`), da cintura para cima, sem boca desenhada:
`explica.png`, `aponta.png`, `joinha.png`, `ok.png`, `cruzado.png`, `duvida.png`, `confiante.png`, `tchau.png`, `comemora.png`.

### Passo 2: Recorte e Rigging
```bash
python3 scripts/recorta.py mascote/src mascote/poses
python3 scripts/rosto.py grade mascote/poses
# Preencha mascote/layout.json com as coordenadas lidas na grade
python3 scripts/rosto.py preparar mascote
python3 scripts/rosto.py folha mascote
```

### Passo 3: Roteiro (`roteiros/meu-video.json`)
```json
{
  "nome": "como-viralizar",
  "hook": "O segredo para prender no primeiro segundo",
  "falas": [
    {"texto": "Para de rolar! Você posta todo dia e ninguém assiste?", "pose": "aponta"},
    {"texto": "O problema não é o algoritmo do Instagram.", "pose": "duvida"},
    {"texto": "É que o seu gancho não entrega o *resultado* de cara.", "pose": "explica"},
    {"texto": "Testa isso no próximo post e me conta!", "pose": "joinha"}
  ]
}
```

### Passo 4: Geração do Vídeo
```bash
python3 scripts/video.py mascote roteiros/como-viralizar.json
```
O vídeo final será compilado em `saida/como-viralizar.mp4` pronto para publicação.

---

## 🤖 Uso com Agentes de IA (Claude Code, Cursor, Antigravity)

Este repositório inclui a especificação completa [`SKILL.md`](./SKILL.md). 
Ao carregar este projeto em qualquer assistente de código, o agente já saberá:
1. Como validar o ambiente e as chaves de API.
2. Como orquestrar as poses, o recorte e a calibração de olhos e boca.
3. Como gerar o áudio e inspecionar a conformidade fonética do lip sync.
4. Como rodar o checklist de qualidade antes da entrega final.

---

## 📄 Licença

Distribuído sob a licença [MIT](./LICENSE). Criado por [Cadu Bezerra](https://github.com/cadubezerrapro).
