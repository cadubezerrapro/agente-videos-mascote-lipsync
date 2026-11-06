<div align="center">

# 🎬 Agente de Vídeos Virais com Mascote & Lip Sync

**Pipeline open-source para criar vídeos verticais virais (Reels · TikTok · Shorts)**\
**com mascote ilustrado, lip sync fonético e legendas palavra a palavra.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-f4d43a.svg)](./LICENSE)
[![Claude Skill](https://img.shields.io/badge/Claude-Skill-blueviolet?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJhMTAgMTAgMCAxIDAgMCAyMCAxMCAxMCAwIDAgMCAwLTIweiIgZmlsbD0iI2ZmZiIvPjwvc3ZnPg==)](./SKILL.md)

<br>

<table>
<tr>
<td width="50%">

### O que ele faz

Transforma uma ideia ou vídeo viral de referência em um **vídeo vertical pronto para postar** com o seu próprio mascote ilustrado — 1080×1920 a 30 fps, com boca sincronizada, voz humana e legenda automática.

</td>
<td width="50%">

### Para quem é

Criadores de conteúdo, agências e devs que querem **escalar produção de vídeo curto** sem editor de vídeo, sem locução manual e sem mensalidade de ferramenta de animação.

</td>
</tr>
</table>

</div>

---

## ⚡ Funcionalidades

| Recurso | Detalhe |
|---|---|
| **9 Poses Expressivas** | Geradas via [Nano Banana](https://www.nanobanana.com/) com fundo liso e consistência de personagem |
| **Voz 100% Humana** | Síntese contínua em chamada única — sem pausas robóticas entre frases |
| **Lip Sync Fonético** | [Rhubarb](https://github.com/DanielSWolf/rhubarb-lip-sync) mapeia 9 formas de boca vetoriais (A–H + X) que acompanham cada fonema |
| **Boca Fecha no Silêncio** | Algoritmo que detecta pausas de áudio e garante zero bocas abertas no silêncio |
| **Legendas Dinâmicas** | Sincronizadas palavra por palavra, com destaque de cor e zoom de câmera na ênfase |
| **Render Determinístico** | [HyperFrames](https://www.npmjs.com/package/hyperframes) compila HTML5 + GSAP direto em MP4 — sem editor de vídeo pesado |
| **3 Provedores de Voz** | Fish Audio, ElevenLabs ou VoiceStudio (100% local e gratuito) |
| **Claude Skill Integrada** | O [`SKILL.md`](./SKILL.md) permite que qualquer agente de IA orquestre toda a pipeline |

---

## 📐 Como funciona

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

## 📂 Estrutura do Projeto

```
agente-videos-mascote-lipsync/
├── SKILL.md              # Especificação completa para agentes de IA
├── README.md             # Este arquivo
├── requirements.txt      # Dependências Python
├── LICENSE               # MIT
└── scripts/
    ├── recorta.py        # Remove fundo e calcula transparência
    ├── rosto.py          # Grade de medição, base sem boca e folha de conferência
    ├── mascote_rig.py    # Stage SVG com 9 bocas vetoriais, pálpebras e respiração
    ├── vozes.py          # Wrapper unificado: Fish Audio · ElevenLabs · VoiceStudio
    └── video.py          # Pipeline de montagem, timeline GSAP e render MP4
```

---

## 🚀 Instalação

### Pré-requisitos

| Ferramenta | Versão mínima | Instalação |
|---|---|---|
| Python | 3.10+ | [python.org](https://www.python.org/) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org/) |
| FFmpeg & FFprobe | — | `sudo apt install ffmpeg` ou [ffmpeg.org](https://ffmpeg.org/) |
| Rhubarb Lip Sync | 1.13+ | [Releases](https://github.com/DanielSWolf/rhubarb-lip-sync/releases) |

### Setup rápido

```bash
# 1. Clone o repositório
git clone https://github.com/cadubezerrapro/agente-videos-mascote-lipsync.git
cd agente-videos-mascote-lipsync

# 2. Instale as dependências Python
pip install -r requirements.txt

# 3. Instale o renderizador e o navegador
npm install -g hyperframes
npx playwright install chromium

# 4. Configure o Rhubarb (Linux/WSL)
git clone --depth 1 https://github.com/DanielSWolf/rhubarb-lip-sync ~/repos/rhubarb-lip-sync
cd ~/repos/rhubarb-lip-sync && mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc) rhubarb
export RHUBARB=$HOME/repos/rhubarb-lip-sync/build/rhubarb/rhubarb

# 5. Configure a chave do provedor de voz (escolha um)
export FISH_API_KEY="sua-chave"          # Fish Audio
export ELEVENLABS_API_KEY="sua-chave"    # ElevenLabs
export VOICESTUDIO_URL="http://127.0.0.1:3900"  # VoiceStudio (local, grátis)
```

---

## 🎙️ Provedores de Voz

| Provedor | Modo | Variável de ambiente | Destaque |
|---|---|---|---|
| **[Fish Audio](https://fish.audio/)** | API nuvem | `FISH_API_KEY` | PT-BR natural, Voice Design e clonagem rápida |
| **[ElevenLabs](https://elevenlabs.io/)** | API nuvem | `ELEVENLABS_API_KEY` | Máxima expressividade e timestamps por palavra |
| **VoiceStudio** | Local | `VOICESTUDIO_URL` | 100% gratuito, sem limite de uso, offline |

---

## 🛠️ Uso Rápido

### 1. Gere as 9 poses no Nano Banana

Crie o mascote em 9 poses com fundo liso monocromático (`#BFE3FF`), da cintura para cima, **sem boca desenhada**:

`explica` · `aponta` · `joinha` · `ok` · `cruzado` · `duvida` · `confiante` · `tchau` · `comemora`

### 2. Recorte e rigging

```bash
python3 scripts/recorta.py mascote/src mascote/poses
python3 scripts/rosto.py grade mascote/poses
# → Preencha mascote/layout.json com as coordenadas
python3 scripts/rosto.py preparar mascote
python3 scripts/rosto.py folha mascote
```

### 3. Escreva o roteiro

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

### 4. Gere o vídeo

```bash
python3 scripts/video.py mascote roteiros/como-viralizar.json
# → saida/como-viralizar.mp4 (1080×1920, 30 fps, pronto para postar)
```

---

## 🤖 Uso com Agentes de IA

Este repositório inclui a especificação completa [`SKILL.md`](./SKILL.md), compatível com **Claude Code**, **Cursor**, **Antigravity** e qualquer assistente que leia arquivos de skill.

Ao carregar o projeto, o agente já sabe:

1. ✅ Validar o ambiente e as chaves de API
2. ✅ Orquestrar poses, recorte e calibração de olhos/boca
3. ✅ Gerar áudio e inspecionar a conformidade fonética do lip sync
4. ✅ Rodar o checklist de qualidade antes da entrega final

**Instalar a skill no Claude:**

```
/plugin install agente-videos-mascote-lipsync@cadubezerrapro
```

---

## 📄 Licença

Distribuído sob a licença [MIT](./LICENSE).

---

<div align="center">

Feito por [**Cadu Bezerra**](https://github.com/cadubezerrapro) · [@OCadubezerra](https://instagram.com/OCadubezerra)

[ia_thefuture](https://ia-thefuture.vercel.app) · [ZuckPay](https://zuckpay.com.br)

</div>
