---
name: agente-videos-mascote-lipsync
description: Use para criar vídeos verticais virais (Reels, TikTok, Shorts) com um mascote ilustrado que fala com lip sync, voz Fish Audio, ElevenLabs ou VoiceStudio e legenda palavra a palavra, clonando o formato de um vídeo viral.
---

# Agente de vídeos virais com mascote falante

Você é o agente de vídeo do usuário. Ele tem (ou vai criar) um mascote ilustrado. Você pega um vídeo viral de referência, entende por que ele prende, escreve um roteiro novo com a mesma estrutura e entrega um MP4 1080x1920 30 fps em que o mascote fala com boca sincronizada, pisca, troca de pose a cada frase e tem legenda palavra a palavra.

Pilha: **Nano Banana** (poses do mascote) → **recorte + marcação do rosto** → **voz: Fish Audio, ElevenLabs ou VoiceStudio** (TTS, criação/clonagem de voz, transcrição) → **Rhubarb Lip Sync** (bocas) → **HyperFrames** (render HTML → MP4). Hypit e OpenCut são opcionais (ver "Ferramentas").

## Regras de ouro (valem para todo vídeo)

1. **Voz 100% humana, sem pausas incomuns.** O roteiro inteiro vai numa única chamada de TTS (a entonação flui como fala real). Nunca gere frase por frase e cole com silêncio fixo: isso cria pausas artificiais e quebra a entonação. Qualquer silêncio interno acima de 0,40 s vira 0,28 s. Pausas finais aceitáveis: entre ~0,15 e 0,40 s.
2. **Áudio por um motor de voz profissional:** Fish Audio, ElevenLabs ou VoiceStudio (escolha em `config.json`). Chaves sempre em variável de ambiente (`FISH_API_KEY`, `ELEVENLABS_API_KEY`, `OMNIVOICE_API_KEY`), nunca em arquivo nem no projeto. Peça a chave ao usuário em cada sessão nova.
3. **Boca fecha no silêncio.** Depois do Rhubarb, qualquer boca aberta que caia numa pausa vira repouso. Conferência obrigatória: 0 bocas abertas em silêncio.
4. **Frame 0 é a thumbnail.** O vídeo abre já com o gancho na tela e o mascote na pose da primeira fala.
5. **Nada sai da tela.** Toda pose cabe entre x 20 e 1060 px; texto só na faixa segura (topo 168 px e rodapé abaixo de 1330 px ficam livres da interface do app, exceto a legenda).
6. **Clone o formato, nunca o conteúdo.** Copie estrutura, ritmo, tipo de gancho e de legenda. Não reutilize áudio, imagens, texto literal nem a cara de ninguém do vídeo original.
7. **Vozes:** não use vozes que imitam pessoas reais, dubladores famosos ou personagens de terceiros. Use vozes genéricas da biblioteca, crie uma com Voice Design, ou clone a voz do próprio usuário (com o consentimento dele).
8. **Feito = assistido.** Só entregue depois do controle de qualidade (seção 7).

## 0. Montar o ambiente (sessão nova)

Domínios que precisam estar liberados na conta (Configurações > Recursos > domínios permitidos): `api.fish.audio` (Fish Audio), `api.elevenlabs.io` (ElevenLabs) e, para baixar referências, `www.instagram.com`. O VoiceStudio roda local e não precisa de domínio. GitHub, npm e PyPI normalmente já vêm liberados. Se uma chamada falhar com `CONNECT tunnel failed 403`, é domínio bloqueado: peça para o usuário liberar, não tente contornar.

```bash
mkdir -p ~/repos && cd ~/repos
git clone --depth 1 https://github.com/DanielSWolf/rhubarb-lip-sync
apt-get install -y libboost-dev            # Rhubarb compila do fonte (binário de release costuma ser bloqueado)
cd rhubarb-lip-sync && sed -i 's/^cmake_policy(SET CMP0167 OLD)/#&/' rhubarb/CMakeLists.txt
mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc) rhubarb
export RHUBARB=$PWD/rhubarb/rhubarb && $RHUBARB --version
npm i -g hyperframes                       # render HTML -> MP4
cd /tmp && npm pack gsap@3.15.0 && tar xzf gsap-3.15.0.tgz && export GSAP_JS=/tmp/package/dist/gsap.min.js  # CDN costuma ser bloqueado
pip install --break-system-packages yt-dlp opencv-python-headless numpy pillow playwright
export HYPERFRAMES_BROWSER_PATH=$(ls /opt/pw-browsers/chromium-*/chrome-linux64/chrome 2>/dev/null | head -1)
# sem esse caminho: npx playwright install chromium e aponte para o chrome instalado
export FISH_API_KEY=...                    # Fish Audio (pedir ao usuário)
export ELEVENLABS_API_KEY=...              # ElevenLabs (pedir ao usuário)
export VOICESTUDIO_URL=http://127.0.0.1:3900   # VoiceStudio local (OMNIVOICE_API_KEY só se for remoto)
```

Grave os scripts da seção "Scripts" em `scripts/`. Estrutura do projeto:

```
meu-projeto/
  scripts/            recorta.py rosto.py mascote_rig.py vozes.py video.py
  mascote/
    src/              as 9 imagens do Nano Banana, nomeadas pela pose (explica.png, aponta.png, ...)
    poses/            recortes + <pose>_base.png (sem boca)
    layout.json       boca e olhos de cada pose
    config.json       voz e cores
  roteiros/           um .json por vídeo
  projetos/           projetos HyperFrames gerados (editáveis)
  saida/              MP4 finais
```

## 1. Criar o mascote: 9 poses no Nano Banana

O usuário escolhe o mascote dele (animal, objeto, personagem original). Nunca use personagem de terceiros. Gere uma **imagem de referência** primeiro (o mascote de frente, corpo até a cintura) e depois as 9 poses, sempre anexando a referência para manter o mesmo personagem.

**Regras para as imagens (é isso que faz o recorte e o lip sync funcionarem):**
- Fundo liso, de uma cor só, que não exista no mascote (ex.: azul-claro #BFE3FF para um mascote laranja; magenta #F0F para um mascote verde). Nada de cenário, sombra no chão, textura ou borda de adesivo.
- Mesmo enquadramento em todas: da cintura para cima, centralizado, de frente, mesma escala, sem cortar mãos ou orelhas.
- **Rosto sem boca desenhada** (área lisa onde ficaria a boca). Se o modelo insistir em desenhar a boca, peça boca fechada pequena e neutra; ela é apagada no passo 2.
- Olhos abertos, bem visíveis. Sem texto, logo ou marca d'água.
- Mínimo 1024 px no lado maior. PNG.

**Prompt base** (cole antes de cada pose, trocando os colchetes):

```
Use a imagem anexada como referência exata do personagem: [descrição curta do mascote, cores, roupa, acessórios].
Mesmo estilo de ilustração, mesmas proporções, mesmas cores e traço.
Enquadramento da cintura para cima, de frente, centralizado, ocupando 80% da altura.
Fundo totalmente liso na cor [#BFE3FF], sem sombra, sem cenário, sem textura, sem borda.
O rosto NÃO tem boca desenhada: a área da boca é lisa, da cor da pele/pelo do rosto. Olhos abertos.
Sem texto, sem logo, sem marca d'água. Pose: [POSE]
```

**As 9 poses** (o nome do arquivo é o nome da pose usado no roteiro):

| Arquivo | [POSE] para o prompt | Quando usar no roteiro |
|---|---|---|
| `explica.png` | as duas mãos à frente do corpo, palmas para cima, explicando com calma | explicação, contexto (pose inicial padrão) |
| `aponta.png` | uma mão levantada com o dedo indicador para cima, a outra mão relaxada na frente da barriga | gancho, chamar atenção, "olha isso" |
| `joinha.png` | dois polegares para cima na altura do peito, expressão animada | aprovação, "funciona", CTA |
| `ok.png` | uma mão fazendo sinal de OK ao lado do rosto, a outra mão fechada no peito | dica certeira, "é isso" |
| `cruzado.png` | braços cruzados no peito, postura confiante | afirmação firme, "simples assim" |
| `duvida.png` | ombros levantados e as duas mãos abertas para os lados, expressão de dúvida | pergunta, problema, "por quê?" |
| `confiante.png` | dois polegares para cima afastados do corpo, olhar confiante de canto | provocação, autoridade |
| `tchau.png` | as duas mãos abertas levantadas, acenando, expressão alegre | final (pose final padrão) |
| `comemora.png` | os dois punhos fechados levantados comemorando, expressão de alegria | resultado, vitória, revelação |

Confira as 9 imagens antes de seguir: mesmo personagem, mesmas cores, mesmo tamanho de cabeça. Refaça a que destoar.

## 2. Recortar, marcar o rosto e conferir

```bash
python3 scripts/recorta.py mascote/src mascote/poses     # tira o fundo (transparência)
python3 scripts/rosto.py grade mascote/poses              # gera mascote/poses/_grade/<pose>.png com régua
```

Abra **cada** imagem de `_grade/` e leia as coordenadas na régua (linhas a cada 25 px, números a cada 100 px). Preencha `mascote/layout.json`:

```json
{
  "explica": {
    "boca":   {"x": 230, "y": 250, "largura": 70},
    "apagar": {"x": 230, "y": 252, "rx": 60, "ry": 30},
    "olhos":  [{"x": 190, "y": 200, "r": 14}, {"x": 272, "y": 200, "r": 14}],
    "pele":   "#a69e93",
    "repouso": "reto"
  }
}
```
- `boca`: centro onde a boca deve ficar e largura de uma boca média do personagem (aprox. 60% da largura do focinho/queixo).
- `apagar`: elipse que cobre a boca desenhada, um pouco maior que ela. Use `null` se a pose veio sem boca. Não encoste no nariz nem passe da borda do rosto.
- `olhos`: centro e raio de cada olho (do olho inteiro, não só da pupila). Mascote com um olho: deixe um item; sem olhos: lista vazia.
- `pele`: cor da pele/pelo em volta dos olhos (é a cor da pálpebra). Tire do pixel ao lado do olho.
- `repouso`: boca quando ele não fala, combinando com a expressão da pose: `sorriso`, `reto` (sério/explicando), `o` (surpresa/dúvida) ou `canto` (sorriso de canto/confiante).

Depois:

```bash
python3 scripts/rosto.py preparar mascote     # cria <pose>_base.png com a boca apagada
python3 scripts/rosto.py folha mascote        # mascote/_folha.png: cada pose com boca X, D, F e piscada
```

Abra `_folha.png` e confira pose por pose: boca no lugar e do tamanho certo (a D bem aberta não pode passar do queixo), nenhum resto da boca antiga, pálpebra cobrindo o olho inteiro sem invadir sobrancelha ou nariz, cor da pálpebra igual à pele. Ajuste o `layout.json` e repita até ficar perfeito. Mudar o tamanho do mascote na tela: `DIST_OLHOS` em `mascote_rig.py`.

## 3. Voz: Fish Audio, ElevenLabs ou VoiceStudio

O motor fica em `mascote/config.json` (`"provedor"`). Os três passam pelo mesmo `vozes.py` e seguem as mesmas regras: roteiro inteiro numa chamada só, pausas limitadas, boca fechando no silêncio.

| Motor | Melhor para | Tempo por palavra (legenda exata) | Custo |
|---|---|---|---|
| `fishaudio` | vozes naturais em PT-BR, Voice Design e clonagem rápida | ASR `/v1/asr` (plano pago); no grátis, alinhamento pelo áudio | plano grátis para TTS |
| `elevenlabs` | vozes muito expressivas, multilíngue | vem junto com o áudio (`with-timestamps`), exato | por caractere, conforme plano |
| `voicestudio` | rodar local, sem custo por uso, privacidade, 646 idiomas | transcrição local com tempo por palavra, exato e grátis | grátis (usa CPU/GPU da máquina) |

**Escolher a voz:**
```bash
python3 scripts/vozes.py vozes fishaudio "masculino"     # biblioteca pública da Fish (prefira autor "Fish Official")
python3 scripts/vozes.py vozes elevenlabs                 # vozes da conta ElevenLabs
python3 scripts/vozes.py vozes voicestudio                # perfis de voz do VoiceStudio
python3 scripts/vozes.py falar fishaudio <voz_id> "Frase do gancho" amostra.wav
```
Gere a frase do gancho em 2 ou 3 vozes e deixe o usuário escolher. Descarte vozes com nome de pessoa famosa, dublador ou personagem.

**Voz exclusiva do mascote:**
- Fish Audio, por descrição (Voice Design): `vozes.py desenhar "voz masculina jovem, simpática e animada, português do Brasil, tom de conversa" vozes/ --n 3`, ouça e salve a escolhida com `vozes.py salvar "Voz do mascote" vozes/candidata_1.wav` (devolve o `voz_id`).
- Clonar a voz do próprio usuário (com consentimento): 1 a 20 amostras limpas, sem música, `vozes.py salvar "Minha voz" a1.wav a2.wav` (Fish), ou crie o perfil no app do VoiceStudio ou na ElevenLabs e use o id.

**Ritmo:** bom para Reels é 2,6 a 3,2 palavras por segundo. Mais rápido soa atropelado: baixe `velocidade` para 0,95.

`mascote/config.json`:
```json
{"provedor": "fishaudio", "voz_id": "<id da voz>", "velocidade": 1.0, "idioma": "pt",
 "pose_inicial": "explica", "pose_final": "tchau",
 "fundo": "#f3ebdd", "cor_destaque": "#ffd23f", "cor_contorno": "#3a2824"}
```
Opcionais por motor: Fish `"modelo": "s2.1-pro-free"` (grátis) ou `"s2.1-pro"`, `"temperatura"`; ElevenLabs `"modelo": "eleven_multilingual_v2"`, `"estabilidade"` (0,45 = mais expressivo), `"estilo"`, `"formato_eleven"`; VoiceStudio `"modelo"` (engine instalada ou `tts-1-hd`), `"instrucoes"` (tags de estilo).

**Alinhamento das legendas**, nesta ordem automática: 1) tempos que vêm com o próprio TTS (ElevenLabs), recalculados depois do encurtamento de pausas; 2) transcrição com tempo por palavra do provedor (VoiceStudio local, Fish pago, ElevenLabs Scribe); 3) sem nenhum dos dois, fronteiras das frases nas pausas reais e palavras distribuídas por sílaba. As trocas de pose ficam exatas em todos os casos; no modo 3 a palavra destacada pode variar alguns centésimos.

## 4. Entender o vídeo viral de referência

1. Obtenha o arquivo: `yt-dlp -o ref.mp4 <link do Instagram>`. TikTok e YouTube costumam estar bloqueados no ambiente: peça o arquivo ao usuário.
2. Meça e veja:
   ```bash
   ffprobe -v error -show_entries format=duration -of csv=p=0 ref.mp4
   ffmpeg -i ref.mp4 -vf "select='gt(scene,0.3)',showinfo" -f null - 2>&1 | grep pts_time   # cortes
   ffmpeg -i ref.mp4 -vf "fps=2,scale=270:-1,tile=6x5" -frames:v 1 grade_ref.png            # grade de frames
   ffmpeg -i ref.mp4 -t 3 -vf "fps=10,scale=270:-1,tile=10x3" -frames:v 1 gancho_ref.png    # os 3 primeiros segundos
   ```
   Fala: transcreva com `vozes.asr` (VoiceStudio local é grátis; Fish e ElevenLabs conforme o plano) ou leia as legendas na grade.
3. Escreva o **mapa do viral** (curto, e mostre ao usuário):
   - **Gancho (0 a 3 s):** o que aparece e o que é dito no primeiro segundo; por que faz parar de rolar (pergunta, provocação, resultado primeiro, erro comum, número).
   - **Estrutura:** ex. problema → virada → prova/explicação → payoff → CTA. Duração de cada bloco.
   - **Ritmo:** segundos por frase/corte, onde acelera.
   - **Legenda:** palavras por tela, cor de destaque, posição.
   - **Por que funciona:** 2 ou 3 linhas.
4. **Roteiro novo** no mesmo esqueleto, sobre o tema do usuário, nas palavras dele. 15 a 35 s, frases curtas (até ~12 palavras por fala), uma pose por fala, gancho no primeiro segundo, CTA no fim. Tom de conversa, sem cara de texto de IA, sem travessão. `*palavra*` destaca (cor + zoom): use 1 ou 2 por vídeo.

```json
{
  "nome": "erro-do-perfil",
  "hook": "O erro que trava seu perfil",
  "falas": [
    {"texto": "Para de rolar! Você posta todo dia e ninguém vê?", "pose": "aponta"},
    {"texto": "O problema não é o algoritmo.", "pose": "duvida"},
    {"texto": "É que os primeiros *três* segundos não prendem ninguém.", "pose": "explica"},
    {"texto": "Começa pelo resultado. Depois explica.", "pose": "ok"},
    {"texto": "Simples assim.", "pose": "cruzado"},
    {"texto": "Salva esse vídeo e testa hoje!", "pose": "joinha"}
  ]
}
```
Mostre o roteiro ao usuário antes de gerar, quando ele estiver presente.

## 5. Gerar o vídeo

```bash
python3 scripts/video.py mascote roteiros/erro-do-perfil.json
```
O script: gera a voz inteira de uma vez → encurta pausas longas → alinha palavras e frases → Rhubarb (`-r phonetic`, funciona em português) → fecha bocas no silêncio → monta o projeto HyperFrames (palco do mascote, gancho, legendas, trocas de pose com antecipação e assentamento, respiração, piscadas) → renderiza em `saida/<nome>.mp4`. Use `--sem-render` para só montar o projeto. O projeto em `projetos/<nome>/` é editável (`npx hyperframes preview`).

## 6. Como o lip sync funciona (para ajustar)

Rhubarb devolve formas de boca no tempo: **A** (M, B, P, lábios fechados), **B** (consoantes, dentes cerrados), **C** (E, É, aberta), **D** (A, bem aberta), **E** (O, arredondada), **F** (U, biquinho), **G** (F, V, dente no lábio), **H** (L, língua), **X** (repouso). Cada pose tem as 9 bocas vetoriais desenhadas por cima da imagem sem boca, na posição e escala do `layout.json`; a timeline liga uma por vez. Pálpebras são elipses da cor da pele com a linha do olho fechado. Para mudar o desenho das bocas (ex.: mascote com bico), edite `bocas()` em `mascote_rig.py` mantendo as 9 formas.

## 7. Controle de qualidade (obrigatório antes de entregar)

```bash
cd projetos/<nome> && npx hyperframes check --json        # 0 erros
```
1. **Pausas:** a linha `[voz]` do `video.py` lista as pausas finais. Todas entre ~0,15 e 0,40 s.
2. **Boca x áudio:** nenhuma boca C, D, E ou H em trecho de silêncio; nenhuma X longa durante fala. (Use `timing.json` + o WAV para conferir.)
3. **Quadros:** `ffmpeg -i saida/<nome>.mp4 -vf "fps=1,scale=180:-1,tile=8x2" -frames:v 1 grade.png`. Olhe: frame 0 com gancho e pose da primeira fala, mascote inteiro na tela, legenda legível, troca de pose sem quadro vazio, pose final.
4. **Boca em close:** `ffmpeg -ss 2 -i saida/<nome>.mp4 -t 3 -vf "fps=10,crop=380:320:350:600,scale=160:-1,tile=8x4" -frames:v 1 boca.png`. Bocas variando com a fala, fechando nas pausas, piscada inteira.
5. Corrija o que aparecer, renderize de novo e só então entregue o MP4 com uma linha sobre o que é.

## 8. Erros comuns

| Sintoma | Causa e solução |
|---|---|
| `CONNECT tunnel failed, response 403` | Domínio bloqueado. Usuário libera em Configurações > Recursos. |
| Fish `400 Reference not found` | `voz_id` errado ou voz removida. Liste de novo com `vozes.py vozes fishaudio`. |
| ElevenLabs `401` / `422` | Chave errada ou campo inválido. `pcm_44100` exige plano Pro: deixe `mp3_44100_128`. |
| ElevenLabs sem `alignment` | O `video.py` cai na transcrição (Scribe) e depois no alinhamento pelo áudio. |
| VoiceStudio `Connection refused` | App/servidor não está rodando ou porta diferente: ajuste `VOICESTUDIO_URL`. |
| VoiceStudio `409 ambiguous_voice` | Dois perfis com o mesmo nome: use o id do perfil em `voz_id`. |
| Fish `402 Payment Required` na ASR | Plano grátis. Normal: o `video.py` alinha pelo áudio. |
| Render: Chrome não encontrado | `export HYPERFRAMES_BROWSER_PATH=<caminho do chrome>`. |
| GSAP não carrega / vídeo parado | CDN bloqueado. `GSAP_JS` apontando para o `gsap.min.js` local. |
| Rhubarb não compila (`CMP0167`, Boost) | `apt-get install libboost-dev` e comentar a linha `cmake_policy(SET CMP0167 OLD)`. |
| Recorte come parte do mascote | Fundo com textura ou da mesma cor do mascote. Refaça no Nano Banana com fundo liso de outra cor. |
| Resto da boca antiga aparece | Aumente `apagar.rx/ry` ou ajuste o centro. |
| Pálpebra torta ou de outra cor | Corrija `olhos[].r`, centro e `pele` no `layout.json`. |
| Pausas longas ou voz "colada" | Nunca gere por frase. Confirme que o roteiro foi numa chamada só e que `MAX_PAUSA` está em 0,40. |
| Mascote pequeno ou grande demais | `DIST_OLHOS` em `mascote_rig.py` (padrão 185). |

## Ferramentas

- **HyperFrames** (heygen-com/hyperframes): renderiza HTML+GSAP em MP4 de forma determinística. Regras que importam: todo elemento temporizado tem `class="clip"`, `data-start`, `data-duration`; uma timeline GSAP pausada registrada em `window.__timelines`; nada de `Date.now()`, `Math.random()` sem semente ou rede. Rode `npx hyperframes check` antes do render.
- **Rhubarb Lip Sync** (DanielSWolf/rhubarb-lip-sync): formas de boca a partir do áudio. Use o reconhecedor `phonetic` para português.
- **Fish Audio** (fish.audio): TTS `POST /v1/tts` (header `model`), ASR `POST /v1/asr`, Voice Design `POST /v1/voice-design` (header `model: voice-design-1`), criar voz `POST /model` (multipart, `type=tts`, `train_mode=fast`), listar vozes `GET /model`.
- **ElevenLabs** (elevenlabs.io): TTS com tempos `POST /v1/text-to-speech/{voice_id}/with-timestamps` (header `xi-api-key`, `model_id: eleven_multilingual_v2`), transcrição `POST /v1/speech-to-text` (`scribe_v1`), vozes `GET /v1/voices`.
- **VoiceStudio** (debpalash/voicestudio): estúdio de voz local (clonagem, design, 646 idiomas, CPU ou GPU). API compatível com OpenAI em `http://127.0.0.1:3900/v1`: `POST /audio/speech`, `POST /audio/transcriptions` (`verbose_json` + `timestamp_granularities[]=word`), `GET /audio/voices`. Instala com `curl -fsSL https://voicestudio.sh/install | sh` ou Docker.
- **Hypit** (hypit-ai/hypit): método bom para ler vídeos de referência (grades de frames ligadas à transcrição); a geração depende do serviço HypiHub, que pode estar bloqueado.
- **OpenCut** (opencut-app/opencut): editor de vídeo para ajustes manuais; API e modo headless ainda em desenvolvimento.

## Scripts

Grave cada bloco no arquivo indicado, dentro de `scripts/`.

### scripts/recorta.py

```python
"""Recorta o mascote do fundo liso (ou texturizado) de cada pose.
Uso: python3 recorta.py mascote/src mascote/poses
Cada arquivo de src (png/jpg/webp) vira <nome>.png com transparência em poses/.
O fundo é estimado pela cor das bordas da imagem; peça imagens com fundo liso de uma cor
que NÃO exista no mascote."""
import cv2, numpy as np, glob, os, sys

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
for f in sorted(glob.glob(os.path.join(src, "*"))):
    im = cv2.imread(f)
    if im is None:
        continue
    h, w = im.shape[:2]
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
    borda = np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])
    med = np.median(borda, 0)
    dist = np.linalg.norm(lab - med, axis=2)
    p97 = float(np.percentile(np.linalg.norm(borda - med, axis=1), 97))
    T = max(14.0, p97 * 1.35)
    liso = p97 < 12  # fundo de cor única (o recomendado)
    cand = (dist < T).astype(np.uint8)
    k = np.ones((7, 7), np.uint8)
    n, lb = cv2.connectedComponents(cv2.erode(cand, k), connectivity=4)  # erosão fecha frestas finas
    edge = set(np.unique(np.concatenate([lb[0], lb[-1], lb[:, 0], lb[:, -1]]))) - {0}
    bg = cv2.dilate(np.isin(lb, list(edge)).astype(np.uint8), k) & cand
    # bolsões de fundo presos entre braço e corpo também saem (só com fundo liso)
    if liso:
        estrito = (dist < max(8.0, p97 * 1.2)).astype(np.uint8)
        n2, l2, st2, _ = cv2.connectedComponentsWithStats(estrito)
        for i in range(1, n2):
            if st2[i, cv2.CC_STAT_AREA] > h * w * 0.002:
                bg[l2 == i] = 1
    sil = ((1 - bg) * 255).astype(np.uint8)
    n3, l3, st3, _ = cv2.connectedComponentsWithStats(sil)
    sil = ((l3 == 1 + np.argmax(st3[1:, cv2.CC_STAT_AREA])) * 255).astype(np.uint8)
    sil = cv2.morphologyEx(sil, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    sil = cv2.erode(sil, np.ones((3, 3), np.uint8))
    x, y, bw, bh = cv2.boundingRect(sil)
    p = 6
    x0, y0, x1, y1 = max(0, x - p), max(0, y - p), min(w, x + bw + p), min(h, y + bh + p)
    rgba = cv2.cvtColor(im, cv2.COLOR_BGR2BGRA)
    rgba[..., 3] = cv2.GaussianBlur(sil, (5, 5), 0)
    nome = os.path.splitext(os.path.basename(f))[0] + ".png"
    cv2.imwrite(os.path.join(out, nome), rgba[y0:y1, x0:x1])
    print(nome, (x1 - x0, y1 - y0))
```

### scripts/rosto.py

```python
"""Marca boca e olhos de cada pose e prepara a base sem boca.

1) python3 rosto.py grade mascote/poses       -> mascote/poses/_grade/<pose>.png (régua a cada 25 px)
   Abra cada grade, ache boca e olhos e preencha mascote/layout.json (modelo abaixo).
2) python3 rosto.py preparar mascote           -> <pose>_base.png (boca apagada, se pedido)
3) python3 rosto.py folha mascote              -> mascote/_folha.png (todas as poses x bocas x piscada)

layout.json (coordenadas em pixels da imagem RECORTADA de cada pose):
{
  "explica": {
    "boca":   {"x": 230, "y": 250, "largura": 70},        centro e largura da boca de repouso
    "apagar": {"x": 230, "y": 252, "rx": 60, "ry": 30},  elipse da boca desenhada (null se a pose já veio sem boca)
    "olhos":  [{"x": 190, "y": 200, "r": 14}, {"x": 272, "y": 200, "r": 14}],
    "pele":   "#a69e93",                                cor em volta dos olhos (pálpebra)
    "repouso": "sorriso"                                sorriso | reto | o | canto
  }, ...
}
"""
import json, os, sys, glob
import numpy as np


def grade(pasta):
    from PIL import Image, ImageDraw
    out = os.path.join(pasta, "_grade"); os.makedirs(out, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(pasta, "*.png"))):
        if f.endswith("_base.png"):
            continue
        im = Image.open(f).convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
        d = ImageDraw.Draw(bg)
        for x in range(0, im.width, 25):
            d.line([(x, 0), (x, im.height)], fill=(255, 0, 0, 90) if x % 100 else (255, 0, 0, 200), width=1)
            if x % 100 == 0: d.text((x + 2, 2), str(x), fill=(200, 0, 0, 255))
        for y in range(0, im.height, 25):
            d.line([(0, y), (im.width, y)], fill=(0, 0, 255, 90) if y % 100 else (0, 0, 255, 200), width=1)
            if y % 100 == 0: d.text((2, y + 2), str(y), fill=(0, 0, 200, 255))
        bg.convert("RGB").save(os.path.join(out, os.path.basename(f)))
        print(os.path.join(out, os.path.basename(f)), im.size)


def preparar(raiz):
    import cv2
    L = json.load(open(os.path.join(raiz, "layout.json")))
    for pose, d in L.items():
        im = cv2.imread(os.path.join(raiz, "poses", pose + ".png"), cv2.IMREAD_UNCHANGED)
        bgr, a = im[..., :3].copy(), im[..., 3]
        e = d.get("apagar")
        if e:
            mask = np.zeros(a.shape, np.uint8)
            cv2.ellipse(mask, (int(e["x"]), int(e["y"])), (int(e["rx"]), int(e["ry"])), 0, 0, 360, 255, -1)
            anel = cv2.dilate(mask, np.ones((25, 25), np.uint8)) - mask
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
            pts = bgr[(anel > 0) & (a > 200)]
            # usa a cor dominante do entorno (ignora contornos escuros)
            pts = pts[cv2.cvtColor(pts[None], cv2.COLOR_BGR2HSV)[0][:, 2] > np.percentile(
                cv2.cvtColor(pts[None], cv2.COLOR_BGR2HSV)[0][:, 2], 35)]
            cor, sd = np.median(pts, 0), pts.std(0).mean() * .6
            ruido = np.random.default_rng(len(pose)).normal(0, sd, bgr.shape)
            fill = cv2.GaussianBlur(np.clip(cor + ruido, 0, 255).astype(np.uint8), (3, 3), 0)
            feat = cv2.GaussianBlur(mask, (15, 15), 0).astype(float)[..., None] / 255
            bgr = (bgr * (1 - feat) + fill * feat).astype(np.uint8)
        cv2.imwrite(os.path.join(raiz, "poses", pose + "_base.png"), np.dstack([bgr, a]))
        print(pose, "ok", "(boca apagada)" if e else "")


def folha(raiz):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import mascote_rig
    from playwright.sync_api import sync_playwright
    out = os.path.join(raiz, "_folha"); os.makedirs(out + "/assets", exist_ok=True)
    palco = mascote_rig.html(raiz, out + "/assets")
    L = json.load(open(os.path.join(raiz, "layout.json")))
    cel = []
    for p in L:
        for b in ("X", "D", "F", "piscada"):
            cel.append(f'<div class="c" data-p="{p}" data-b="{b}"><i>{p} {b}</i><div class="in">{palco}</div></div>')
    doc = f'''<html><body style="margin:0;background:#2b78c8;font:12px sans-serif"><style>
.c{{display:inline-block;width:300px;height:330px;overflow:hidden;position:relative}} .c i{{position:absolute;z-index:9;color:#fff}}
.in{{position:absolute;left:0;top:0;width:1080px;height:1920px;transform:scale(.5) translate(-240px,-430px);transform-origin:0 0}}
</style>{"".join(cel)}<script>
document.querySelectorAll('.c').forEach(c=>{{
 c.querySelectorAll('.k-pose').forEach(g=>g.style.opacity=g.id==='k-p-'+c.dataset.p?1:0);
 const b=c.dataset.b;
 if(b==='piscada') c.querySelectorAll('.lids').forEach(l=>l.setAttribute('opacity',1));
 else c.querySelectorAll('[class^=m-]').forEach(m=>m.setAttribute('opacity',m.getAttribute('class')==='m-'+b?1:0));
}});</script></body></html>'''
    open(out + "/index.html", "w").write(doc)
    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page(viewport={"width": 1200, "height": 900})
        pg.goto("file://" + os.path.abspath(out + "/index.html")); pg.wait_for_timeout(500)
        pg.screenshot(path=os.path.join(raiz, "_folha.png"), full_page=True); br.close()
    print(os.path.join(raiz, "_folha.png"))


if __name__ == "__main__":
    {"grade": grade, "preparar": preparar, "folha": folha}[sys.argv[1]](sys.argv[2])
```

### scripts/mascote_rig.py

```python
"""Palco do mascote: as poses (PNG sem boca) + 9 bocas do Rhubarb + pálpebras, todas na mesma
escala e posição no quadro 1080x1920. Funciona com qualquer mascote descrito em layout.json.

Seletores para animar:
  #k-p-<pose>  pose (opacity 0/1)   .m-<A..H|X>  bocas   .lids  piscada   #k-stage  palco inteiro
"""
import json, os, shutil

DIST_OLHOS = 185          # distância entre os olhos no quadro final (px): define o tamanho do mascote
ANCORA = (540, 760)       # onde fica o meio dos olhos
LARG_MAX = 1040           # nenhuma pose passa disso de largura
CONTORNO, BOCA, LINGUA, DENTES = "#3a2824", "#6b2b30", "#ea8a8c", "#fbf8f2"


def bocas(repouso="sorriso", cor=CONTORNO):
    st = f'stroke="{cor}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"'
    rep = {
        "sorriso": f'<path d="M-26,-6 Q-12,8 0,8 Q12,8 26,-6" fill="none" {st}/>',
        "reto": f'<path d="M-18,4 Q0,2 18,4" fill="none" {st}/>',
        "o": (f'<path d="M-14,4 Q0,-4 14,4 Q12,14 0,15 Q-12,14 -14,4Z" fill="{BOCA}" {st}/>'
              f'<path d="M-8,11 Q0,6 8,11 Q0,15 -8,11Z" fill="{LINGUA}"/>'),
        "canto": f'<path d="M-24,-2 Q-6,10 6,6 Q18,2 26,-8" fill="none" {st}/>',
    }
    m = {
        "X": rep.get(repouso, rep["sorriso"]),                                                   # repouso
        "A": f'<path d="M-20,3 Q0,7 20,3" fill="none" {st} stroke-width="5"/>',                # M B P
        "B": (f'<path d="M-24,-3 Q0,1 24,-3 Q20,13 0,14 Q-20,13 -24,-3Z" fill="{BOCA}" {st}/>'  # consoantes
              f'<path d="M-20,-1 Q0,2 20,-1 L18,5 Q0,7 -18,5Z" fill="{DENTES}"/>'),
        "C": (f'<path d="M-27,-4 Q0,0 27,-4 Q24,24 0,26 Q-24,24 -27,-4Z" fill="{BOCA}" {st}/>'  # E, É
              f'<path d="M-14,18 Q0,8 14,18 Q0,26 -14,18Z" fill="{LINGUA}"/>'
              f'<path d="M-22,-2 Q0,1 22,-2 L20,4 Q0,6 -20,4Z" fill="{DENTES}"/>'),
        "D": (f'<path d="M-30,-6 Q0,-2 30,-6 Q28,36 0,39 Q-28,36 -30,-6Z" fill="{BOCA}" {st}/>'  # A aberto
              f'<path d="M-17,29 Q0,15 17,29 Q0,39 -17,29Z" fill="{LINGUA}"/>'
              f'<path d="M-25,-4 Q0,-1 25,-4 L23,3 Q0,5 -23,3Z" fill="{DENTES}"/>'),
        "E": (f'<path d="M-20,-4 Q0,-8 20,-4 Q24,16 0,24 Q-24,16 -20,-4Z" fill="{BOCA}" {st}/>'  # O, Ó
              f'<path d="M-11,16 Q0,9 11,16 Q0,22 -11,16Z" fill="{LINGUA}"/>'),
        "F": f'<ellipse cx="0" cy="6" rx="10" ry="11" fill="{BOCA}" {st}/>',                    # U, biquinho
        "G": (f'<path d="M-22,-2 Q0,2 22,-2 Q18,12 0,13 Q-18,12 -22,-2Z" fill="{BOCA}" {st}/>'  # F V
              f'<path d="M-15,-1 L15,-1 L14,8 Q0,10 -14,8Z" fill="{DENTES}" stroke="{cor}" stroke-width="2"/>'),
        "H": (f'<path d="M-26,-4 Q0,0 26,-4 Q23,26 0,28 Q-23,26 -26,-4Z" fill="{BOCA}" {st}/>'  # L
              f'<path d="M-12,6 Q0,-4 12,6 Q12,18 0,20 Q-12,18 -12,6Z" fill="{LINGUA}"/>'),
    }
    return "".join(f'<g class="m-{k}" opacity="{1 if k == "X" else 0}">{v}</g>' for k, v in m.items())


def html(raiz, assets_dir, pose_inicial=None):
    L = json.load(open(os.path.join(raiz, "layout.json")))
    cfg = json.load(open(os.path.join(raiz, "config.json"))) if os.path.exists(os.path.join(raiz, "config.json")) else {}
    cor = cfg.get("cor_contorno", CONTORNO)
    pose_inicial = pose_inicial or cfg.get("pose_inicial") or next(iter(L))
    os.makedirs(assets_dir, exist_ok=True)
    from PIL import Image
    grupos = []
    for p, d in L.items():
        arq = p + "_base.png"
        src = os.path.join(raiz, "poses", arq)
        shutil.copy(src, os.path.join(assets_dir, arq))
        w, h = Image.open(src).size
        olhos, b = d.get("olhos", []), d["boca"]
        if len(olhos) >= 2:
            dist = abs(olhos[1]["x"] - olhos[0]["x"]) or 1
            s = DIST_OLHOS / dist
            ax, ay = (olhos[0]["x"] + olhos[1]["x"]) / 2, (olhos[0]["y"] + olhos[1]["y"]) / 2
        else:  # mascote com um olho ou sem olhos: usa a boca como régua
            s = (DIST_OLHOS * .55) / b["largura"]
            ax, ay = b["x"], b["y"] - b["largura"]
        s = min(s, LARG_MAX / w)
        left, top = ANCORA[0] - ax * s, ANCORA[1] - ay * s
        W, H = w * s, h * s
        left = min(max(left, 20), 1060 - W)
        ms = b["largura"] / 52
        lids = ""
        for o in olhos:
            r = o["r"] * 1.18
            lids += (f'<ellipse cx="{o["x"]}" cy="{o["y"]}" rx="{r:.1f}" ry="{r * 1.08:.1f}" fill="{d.get("pele", "#999")}"/>'
                     f'<path d="M{o["x"] - r * .9:.1f},{o["y"] + r * .15:.1f} Q{o["x"]},{o["y"] + r * .75:.1f} '
                     f'{o["x"] + r * .9:.1f},{o["y"] + r * .15:.1f}" fill="none" stroke="{cor}" '
                     f'stroke-width="{max(3, r * .22):.1f}" stroke-linecap="round"/>')
        grupos.append(f'''
    <div id="k-p-{p}" class="k-pose" style="position:absolute;left:{left:.1f}px;top:{top:.1f}px;width:{W:.1f}px;height:{H:.1f}px;opacity:{1 if p == pose_inicial else 0}">
      <img src="assets/{arq}" style="position:absolute;inset:0;width:100%;height:100%" />
      <svg viewBox="0 0 {w} {h}" style="position:absolute;inset:0;width:100%;height:100%;overflow:visible">
        <g class="lids" opacity="0">{lids}</g>
        <g transform="translate({b['x']},{b['y']}) scale({ms:.3f})">{bocas(d.get("repouso", "sorriso"), cor)}</g>
      </svg>
    </div>''')
    return f'<div id="k-stage" style="position:absolute;inset:0">{"".join(grupos)}\n  </div>'
```

### scripts/vozes.py

```python
"""Motores de voz com a mesma interface: Fish Audio, ElevenLabs e VoiceStudio (local).
O motor vem de config.json -> "provedor": "fishaudio" | "elevenlabs" | "voicestudio".

Chaves só em variáveis de ambiente (nunca em arquivo):
  FISH_API_KEY            Fish Audio
  ELEVENLABS_API_KEY      ElevenLabs
  VOICESTUDIO_URL         VoiceStudio (padrão http://127.0.0.1:3900); OMNIVOICE_API_KEY só se for remoto

tts(texto, saida_wav, cfg) -> lista de palavras com tempo [{"text","start","end"}] ou None
asr(wav, cfg)              -> lista de palavras com tempo (levanta erro se o motor/plano não tiver)

CLI:
  python3 vozes.py vozes fishaudio "masculino"          lista vozes (fishaudio busca na biblioteca)
  python3 vozes.py vozes elevenlabs                      vozes da sua conta ElevenLabs
  python3 vozes.py vozes voicestudio                     perfis de voz do VoiceStudio
  python3 vozes.py falar <provedor> <voz_id> "Texto" saida.wav
  python3 vozes.py desenhar "descrição da voz" pasta/ --n 3     Voice Design (Fish Audio)
  python3 vozes.py salvar "Nome" amostra1.wav [amostra2.wav]   clona/salva voz na Fish Audio
"""
import json, os, sys, uuid, base64, subprocess, urllib.request, urllib.parse

FISH = "https://api.fish.audio"
ELEVEN = os.environ.get("ELEVENLABS_URL", "https://api.elevenlabs.io")
VSTUDIO = os.environ.get("VOICESTUDIO_URL", "http://127.0.0.1:3900")


# ---------- HTTP ----------
def _req(url, body=None, headers=None, method=None, timeout=300):
    data = json.dumps(body).encode() if isinstance(body, (dict, list)) else body
    h = dict(headers or {})
    if isinstance(body, (dict, list)):
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=h, method=method or ("POST" if data else "GET"))
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return resp.read()


def _multipart(url, campos, arquivos, headers=None, timeout=300):
    b = uuid.uuid4().hex
    p = [f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in campos]
    for k, c in arquivos:
        p.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{os.path.basename(c)}"\r\n'
                 f'Content-Type: application/octet-stream\r\n\r\n'.encode() + open(c, "rb").read() + b"\r\n")
    p.append(f"--{b}--\r\n".encode())
    h = {**(headers or {}), "Content-Type": f"multipart/form-data; boundary={b}"}
    return json.loads(_req(url, b"".join(p), h, "POST", timeout))


def _para_wav(src, dst):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-ac", "1", "-ar", "44100", dst], check=True)


def _palavras_de_caracteres(al):
    """ElevenLabs: alinhamento por caractere -> palavras com tempo."""
    out, cur, s, e = [], "", None, None
    for ch, a, b in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if ch.isspace():
            if cur: out.append({"text": cur, "start": s, "end": e})
            cur, s = "", None
        else:
            if s is None: s = a
            cur += ch; e = b
    if cur: out.append({"text": cur, "start": s, "end": e})
    return out


# ---------- Fish Audio ----------
def _fish_h():
    return {"Authorization": f"Bearer {os.environ['FISH_API_KEY']}"}


def fish_tts(texto, wav, cfg):
    body = {"text": texto, "reference_id": cfg["voz_id"], "format": "wav", "sample_rate": 44100,
            "latency": "normal", "temperature": cfg.get("temperatura", 0.75), "top_p": cfg.get("top_p", 0.75),
            "prosody": {"speed": cfg.get("velocidade", 1.0), "volume": 0, "normalize_loudness": True}}
    open(wav + ".tmp", "wb").write(_req(f"{FISH}/v1/tts", body,
                                        {**_fish_h(), "model": cfg.get("modelo", "s2.1-pro-free")}))
    _para_wav(wav + ".tmp", wav); os.remove(wav + ".tmp")
    return None


def fish_asr(wav, cfg):  # plano pago (no grátis: HTTP 402)
    r = _multipart(f"{FISH}/v1/asr", [("language", cfg.get("idioma", "pt")), ("ignore_timestamps", "false")],
                   [("audio", wav)], {**_fish_h(), "model": "transcribe-1-pro"})
    return [{"text": s["text"], "start": s["start"], "end": s["end"]} for s in r.get("segments", [])]


def fish_vozes(termo="", idioma="pt"):
    q = urllib.parse.urlencode({"title": termo, "language": idioma, "page_size": 30, "sort_by": "task_count"})
    itens = json.loads(_req(f"{FISH}/model?{q}", headers=_fish_h())).get("items", [])
    return [(m["_id"], m["title"], m.get("task_count"), ",".join(m.get("tags", []))[:70]) for m in itens]


def fish_desenhar(instrucao, pasta, n=3, idioma="pt", previa=None):
    os.makedirs(pasta, exist_ok=True)
    body = {"instruction": instrucao, "language": idioma, "n": n}
    if previa: body["reference_text"] = previa[:150]
    r = json.loads(_req(f"{FISH}/v1/voice-design", body, {**_fish_h(), "model": "voice-design-1"}))
    out = []
    for c in r.get("candidates", []):
        p = os.path.join(pasta, f"candidata_{c.get('index', len(out))}.wav")
        open(p, "wb").write(base64.b64decode(c["audio_base64"])); out.append(p)
    return out


def fish_salvar(titulo, *amostras):
    campos = [("type", "tts"), ("title", titulo), ("train_mode", "fast"), ("visibility", "private")]
    return _multipart(f"{FISH}/model", campos, [("voices", a) for a in amostras], _fish_h())["_id"]


# ---------- ElevenLabs ----------
def _el_h():
    return {"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}


def eleven_tts(texto, wav, cfg):
    """Devolve as palavras com tempo (vem junto com o áudio: alinhamento exato e grátis)."""
    body = {"text": texto, "model_id": cfg.get("modelo", "eleven_multilingual_v2"),
            "language_code": cfg.get("idioma", "pt"),
            "voice_settings": {"stability": cfg.get("estabilidade", 0.45), "similarity_boost": 0.8,
                               "style": cfg.get("estilo", 0.25), "use_speaker_boost": True,
                               "speed": cfg.get("velocidade", 1.0)}}
    fmt = cfg.get("formato_eleven", "mp3_44100_128")  # pcm_44100 exige plano Pro
    r = json.loads(_req(f"{ELEVEN}/v1/text-to-speech/{cfg['voz_id']}/with-timestamps?output_format={fmt}",
                        body, _el_h()))
    open(wav + ".tmp", "wb").write(base64.b64decode(r["audio_base64"]))
    _para_wav(wav + ".tmp", wav); os.remove(wav + ".tmp")
    al = r.get("alignment") or r.get("normalized_alignment")
    return _palavras_de_caracteres(al) if al else None


def eleven_asr(wav, cfg):
    r = _multipart(f"{ELEVEN}/v1/speech-to-text", [("model_id", "scribe_v1"), ("language_code", cfg.get("idioma", "pt"))],
                   [("file", wav)], _el_h())
    return [{"text": w["text"], "start": w["start"], "end": w["end"]} for w in r.get("words", []) if w.get("type") == "word"]


def eleven_vozes():
    r = json.loads(_req(f"{ELEVEN}/v1/voices", headers=_el_h()))
    return [(v["voice_id"], v["name"], v.get("category"), json.dumps(v.get("labels", {}), ensure_ascii=False)[:70])
            for v in r.get("voices", [])]


# ---------- VoiceStudio (local, API compatível com OpenAI) ----------
def _vs_h():
    k = os.environ.get("OMNIVOICE_API_KEY")
    return {"Authorization": f"Bearer {k}"} if k else {}


def voicestudio_tts(texto, wav, cfg):
    body = {"model": cfg.get("modelo", "tts-1-hd"), "voice": cfg["voz_id"], "input": texto,
            "response_format": "wav", "speed": cfg.get("velocidade", 1.0)}
    if cfg.get("instrucoes"):
        body["instructions"] = cfg["instrucoes"]
    open(wav + ".tmp", "wb").write(_req(f"{VSTUDIO}/v1/audio/speech", body, _vs_h(), timeout=900))
    _para_wav(wav + ".tmp", wav); os.remove(wav + ".tmp")
    return None


def voicestudio_asr(wav, cfg):  # local e grátis, com tempo por palavra
    r = _multipart(f"{VSTUDIO}/v1/audio/transcriptions",
                   [("model", "whisper-1"), ("language", cfg.get("idioma", "pt")),
                    ("response_format", "verbose_json"), ("timestamp_granularities[]", "word")],
                   [("file", wav)], _vs_h(), timeout=900)
    return [{"text": w["word"], "start": w["start"], "end": w["end"]} for w in r.get("words", [])]


def voicestudio_vozes():
    r = json.loads(_req(f"{VSTUDIO}/v1/audio/voices", headers=_vs_h()))
    itens = r.get("voices", r) if isinstance(r, dict) else r
    return [(v.get("voice_id") or v.get("id"), v.get("name"), "", "") for v in itens]


# ---------- interface única ----------
_TTS = {"fishaudio": fish_tts, "elevenlabs": eleven_tts, "voicestudio": voicestudio_tts}
_ASR = {"fishaudio": fish_asr, "elevenlabs": eleven_asr, "voicestudio": voicestudio_asr}


def tts(texto, wav, cfg):
    return _TTS[cfg.get("provedor", "fishaudio")](texto, wav, cfg)


def asr(wav, cfg):
    return _ASR[cfg.get("provedor", "fishaudio")](wav, cfg)


if __name__ == "__main__":
    cmd, *a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if cmd == "vozes":
        prov = a[0]
        lst = fish_vozes(a[1] if len(a) > 1 else "") if prov == "fishaudio" else \
            eleven_vozes() if prov == "elevenlabs" else voicestudio_vozes()
        for linha in lst: print(*linha, sep=" | ")
    elif cmd == "falar":
        tts(a[2], a[3], {"provedor": a[0], "voz_id": a[1]}); print(a[3])
    elif cmd == "desenhar":
        print(*fish_desenhar(a[0], a[1], int(opt("--n", 3))), sep="\n")
    elif cmd == "salvar":
        print(fish_salvar(a[0], *a[1:]))
```

### scripts/video.py

```python
#!/usr/bin/env python3
"""Roteiro -> vídeo vertical 1080x1920 com o mascote falando (voz Fish Audio, ElevenLabs ou VoiceStudio
+ lip sync Rhubarb + HyperFrames).

Uso: python3 video.py <pasta_do_mascote> roteiros/<nome>.json [--sem-render]

roteiro.json:
{
  "nome": "erro-do-perfil",
  "hook": "Texto do gancho (aparece no frame 0)",
  "falas": [
    {"texto": "Para de rolar! Você posta todo dia e ninguém vê?", "pose": "aponta"},
    {"texto": "É que os primeiros *três* segundos não prendem.", "pose": "explica"}
  ]
}
*palavra* = destaque na legenda + zoom de câmera.
<pasta_do_mascote>/config.json: {"provedor": "fishaudio", "voz_id": "...", "pose_inicial": "explica",
                                  "pose_final": "tchau", "fundo": "#f3ebdd", "cor_destaque": "#ffd23f", "velocidade": 1.0}
Requer a chave do provedor (FISH_API_KEY / ELEVENLABS_API_KEY / VoiceStudio rodando), RHUBARB (binário),
GSAP_JS (gsap.min.js local), HYPERFRAMES_BROWSER_PATH.
"""
import json, os, re, sys, shutil, subprocess, html, random, difflib, unicodedata, wave
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import vozes, mascote_rig

RHUBARB = os.environ.get("RHUBARB", os.path.expanduser("~/repos/rhubarb-lip-sync/build/rhubarb/rhubarb"))
GSAP = os.environ.get("GSAP_JS", "/tmp/package/dist/gsap.min.js")
W, H, FPS = 1080, 1920, 30
MAX_PAUSA, PAUSA_ALVO, LEAD = 0.40, 0.28, 0.25


def sh(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def dur(p):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).strip())


limpa = lambda t: t.replace("*", "")
enfase = lambda w: w.startswith("*") or w.rstrip(".,!?;:").endswith("*")


def le_wav(p):
    w = wave.open(p)
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32), w.getframerate()


def energia(a, sr, db=-36):
    hop = int(sr * .01); n = len(a) // hop
    e = np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(1))
    return e > max(e.max() * 10 ** (db / 20), 60), n


def aperta_pausas(src, dst):
    """Corta as pontas e encurta qualquer silêncio interno > MAX_PAUSA (sem pausas incomuns)."""
    a, sr = le_wav(src); hop = int(sr * .01)
    voz, n = energia(a, sr, -38)
    idx = np.nonzero(voz)[0]
    out, ini, cortes, k = [], max(0, idx[0] - 3) * hop, [], idx[0]
    mapa = [(0.0, ini / sr)]  # (instante original do corte, segundos removidos)
    while k <= idx[-1]:
        if not voz[k]:
            j = k
            while j <= idx[-1] and not voz[j]: j += 1
            if (j - k) * .01 > MAX_PAUSA:
                keep = int(PAUSA_ALVO / .01)
                out.append(a[ini:(k + keep // 2) * hop]); ini = (j - keep // 2) * hop
                cortes.append(float(round((j - k) * .01, 2)))
                mapa.append(((k + keep // 2) * .01, (j - k - 2 * (keep // 2)) * .01))
            k = j
        else:
            k += 1
    out.append(a[ini:min(n, idx[-1] + 6) * hop])
    f = int(sr * .008)
    for s in out:
        if len(s) > 2 * f:
            s[:f] *= np.linspace(0, 1, f); s[-f:] *= np.linspace(1, 0, f)
    y = np.concatenate(out).clip(-32768, 32767).astype(np.int16)
    o = wave.open(dst, "wb"); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes(y.tobytes())
    return cortes, mapa


def remapeia(t, mapa):
    """Converte um tempo do áudio original para o áudio com pausas encurtadas."""
    return max(0.0, t - sum(rem for ini, rem in mapa if ini <= t))


def pausas(p):
    a, sr = le_wav(p); voz, n = energia(a, sr)
    idx = np.nonzero(voz)[0]; g, k = [], idx[0]
    while k < idx[-1]:
        if not voz[k]:
            j = k
            while not voz[j]: j += 1
            if j - k >= 8: g.append(float(round((j - k) * .01, 2)))
            k = j
        else:
            k += 1
    return g


def norm(w):
    w = unicodedata.normalize("NFD", limpa(w).lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in w if unicodedata.category(c) != "Mn"))


def silabas(w):
    return max(1, len(re.findall(r"[aeiouy]+", norm(w))))


def alinha_palavras(rot, seg, wav):
    """Casa as palavras do roteiro com palavras que já têm tempo (ASR ou alinhamento do TTS)."""
    toks = [(w, i) for i, f in enumerate(rot["falas"]) for w in f["texto"].split()]
    A, B = [norm(w) for w, _ in toks], [norm(s["text"]) for s in seg]
    t = [None] * len(A)
    for bl in difflib.SequenceMatcher(None, A, B, autojunk=False).get_matching_blocks():
        for d in range(bl.size):
            t[bl.a + d] = (seg[bl.b + d]["start"], seg[bl.b + d]["end"])
    T, i = dur(wav), 0
    while i < len(t):  # interpola o que não casou
        if t[i] is None:
            j = i
            while j < len(t) and t[j] is None: j += 1
            a0 = t[i - 1][1] if i else 0.0
            a1 = t[j][0] if j < len(t) else T
            for k in range(i, j):
                t[k] = (a0 + (a1 - a0) * (k - i) / (j - i), a0 + (a1 - a0) * (k - i + 1) / (j - i))
            i = j
        else:
            i += 1
    pal = [{"w": w, "s": s, "e": e, "f": f, "enf": enfase(w)} for (w, f), (s, e) in zip(toks, t)]
    segs = []
    for i, f in enumerate(rot["falas"]):
        ws = [p for p in pal if p["f"] == i]
        segs.append({**f, "s": ws[0]["s"], "e": ws[-1]["e"]})
    return segs, pal


def alinha_audio(rot, wav):
    """Plano grátis: fronteiras das falas nas pausas reais; palavras por sílaba nos trechos com voz."""
    a, sr = le_wav(wav); voz, n = energia(a, sr)
    gaps, k = [], 0
    while k < n:
        if not voz[k]:
            j = k
            while j < n and not voz[j]: j += 1
            if j - k >= 8 and 0 < k and j < n: gaps.append((k * .01, j * .01))
            k = j
        else:
            k += 1
    T = n * .01
    pesos = [sum(silabas(x) for x in f["texto"].split()) + 1 for f in rot["falas"]]
    cum = np.cumsum(pesos) / sum(pesos)
    lim, usado = [], -1
    for i in range(len(pesos) - 1):
        alvo = cum[i] * T
        c = [(abs((g[0] + g[1]) / 2 - alvo) - (g[1] - g[0]) * 2, gi) for gi, g in enumerate(gaps) if gi > usado]
        if c:
            _, usado = min(c); lim.append(gaps[usado])
        else:
            lim.append((alvo, alvo))
    inis, fins = [0.0] + [l[1] for l in lim], [l[0] for l in lim] + [T]
    pal, segs = [], []
    for i, f in enumerate(rot["falas"]):
        s0, s1 = inis[i], fins[i]
        tv = np.nonzero(voz[int(s0 / .01):int(s1 / .01)])[0] * .01 + s0
        toks = f["texto"].split(); ws = [silabas(t) for t in toks]
        acc = np.concatenate([[0], np.cumsum(ws)]) / sum(ws)
        for t, a0, a1 in zip(toks, acc[:-1], acc[1:]):
            st = float(tv[min(len(tv) - 1, int(a0 * len(tv)))]) if len(tv) else s0 + a0 * (s1 - s0)
            en = float(tv[min(len(tv) - 1, max(0, int(a1 * len(tv)) - 1))]) + .01 if len(tv) else s0 + a1 * (s1 - s0)
            pal.append({"w": t, "s": st, "e": en, "f": i, "enf": enfase(t)})
        segs.append({**f, "s": s0, "e": s1})
    return segs, pal


def fecha_boca_no_silencio(cues, wav):
    a, sr = le_wav(wav); ref = np.sqrt((a ** 2).mean()); out = []
    for q in cues:
        x = a[int(q["start"] * sr):int(q["end"] * sr)]
        if q["value"] not in "AX" and (np.sqrt((x ** 2).mean()) if len(x) else 0) < ref * .06:
            q = dict(q, value="X")
        if out and out[-1]["value"] == q["value"]:
            out[-1]["end"] = q["end"]
        else:
            out.append(q)
    return out


def paginas(pal, maxw=3):
    pags, cur = [], []
    for i, p in enumerate(pal):
        cur.append(p)
        troca_fala = i + 1 < len(pal) and pal[i + 1]["f"] != p["f"]
        if len(cur) >= maxw or re.search(r"[.!?,]$", limpa(p["w"])) or troca_fala:
            pags.append(cur); cur = []
    return pags + ([cur] if cur else [])


def main():
    raiz, rot_path = sys.argv[1], sys.argv[2]
    cfg = json.load(open(os.path.join(raiz, "config.json")))
    rot = json.load(open(rot_path))
    nome = rot.get("nome", "video")
    proj = os.path.join(os.path.dirname(os.path.abspath(raiz)), "projetos", nome)
    os.makedirs(os.path.join(proj, "assets"), exist_ok=True)
    shutil.copy(GSAP, os.path.join(proj, "assets", "gsap.min.js"))

    # 1) voz: roteiro INTEIRO numa chamada (entonação contínua), pausas limitadas
    texto = " ".join(t if re.search(r"[.!?…]$", t) else t + "." for t in (limpa(f["texto"]).strip() for f in rot["falas"]))
    bruto, limpo, full = (os.path.join(proj, x) for x in ("voz_bruta.wav", "voz_limpa.wav", "assets/voz.wav"))
    prov = cfg.get("provedor", "fishaudio")
    pal_tts = vozes.tts(texto, bruto, cfg)
    cortes, mapa = aperta_pausas(bruto, limpo)
    sh(["ffmpeg", "-y", "-i", limpo, "-af", f"adelay={int(LEAD * 1000)}", "-ac", "1", "-ar", "44100", full])
    # alinhamento: 1) tempos que vieram com o TTS (ElevenLabs)  2) ASR do provedor  3) pelo próprio áudio
    if pal_tts:
        pal_tts = [dict(w, start=remapeia(w["start"], mapa), end=remapeia(w["end"], mapa)) for w in pal_tts]
        segs, pal = alinha_palavras(rot, pal_tts, limpo); modo = f"{prov}: tempos do próprio TTS"
    else:
        try:
            segs, pal = alinha_palavras(rot, vozes.asr(limpo, cfg), limpo); modo = f"{prov}: ASR com tempo por palavra"
        except Exception as e:
            segs, pal = alinha_audio(rot, limpo); modo = f"{prov}: alinhado pelo áudio ({str(e)[:30]})"
    for x in pal + segs:
        x["s"] += LEAD; x["e"] += LEAD
    total = dur(full) + 0.6

    # 2) lip sync
    cues = json.loads(sh([RHUBARB, "-r", "phonetic", "-f", "json", "--extendedShapes", "GHX", full]))["mouthCues"]
    cues = fecha_boca_no_silencio(cues, full)
    json.dump({"segs": segs, "palavras": pal, "bocas": cues, "total": total},
              open(os.path.join(proj, "timing.json"), "w"), ensure_ascii=False, indent=1)

    # 3) timeline
    dest, fundo = cfg.get("cor_destaque", "#ffd23f"), cfg.get("fundo", "#f3ebdd")
    pags, js, caps = paginas(pal), [], []
    for pi, pg in enumerate(pags):
        s = pg[0]["s"]; e = pags[pi + 1][0]["s"] if pi + 1 < len(pags) else total
        spans = "".join(f'<span id="w{pi}_{wi}" class="w">{html.escape(limpa(p["w"]))}</span> ' for wi, p in enumerate(pg))
        caps.append(f'<div id="cap{pi}" class="clip cap" data-start="{s:.3f}" data-duration="{e - s:.3f}" data-track-index="3"><div id="capin{pi}" class="capin">{spans}</div></div>')
        js.append(f'tl.fromTo("#capin{pi}",{{scale:.82,y:18}},{{scale:1,y:0,duration:.14,ease:"back.out(3)"}},{s:.3f});')
        for wi, p in enumerate(pg):
            js.append(f'tl.set("#w{pi}_{wi}",{{color:"{dest}"}},{p["s"]:.3f});')
            if p["enf"]:
                js.append(f'tl.to("#cam",{{scale:1.09,duration:.12,ease:"power3.out"}},{p["s"]:.3f});')
                js.append(f'tl.to("#cam",{{scale:1,duration:.5,ease:"power2.inOut"}},{p["e"] + .15:.3f});')
            else:
                js.append(f'tl.set("#w{pi}_{wi}",{{color:"#ffffff"}},{p["e"]:.3f});')
    prev = "X"
    for c in cues:
        if c["value"] != prev:
            js.append(f'tl.set(".m-{prev}",{{opacity:0}},{c["start"]:.3f});tl.set(".m-{c["value"]}",{{opacity:1}},{c["start"]:.3f});')
            prev = c["value"]
    O = 'transformOrigin:"540px 1700px"'
    pose = segs[0].get("pose", cfg.get("pose_inicial"))
    for k, sg in enumerate(segs):
        p, tt = sg.get("pose", pose), max(0.0, sg["s"] - .12)
        if k and p != pose:
            js.append(f'tl.to("#k-stage",{{scaleY:.97,scaleX:1.02,duration:.08,{O}}},{tt:.3f});')
            js.append(f'tl.set("#k-p-{pose}",{{opacity:0}},{tt + .08:.3f});tl.set("#k-p-{p}",{{opacity:1}},{tt + .08:.3f});')
            js.append(f'tl.to("#k-stage",{{scaleY:1,scaleX:1,duration:.35,ease:"elastic.out(1,.5)",{O}}},{tt + .08:.3f});')
        pose = p
        js.append(f'tl.to("#k-stage",{{rotation:{[-1.6, 1.4, -1, 1.6][k % 4]},duration:.45,ease:"sine.inOut",{O}}},{sg["s"]:.3f});')
    fim = cfg.get("pose_final")
    if fim and fim != pose:
        js.append(f'tl.set("#k-p-{pose}",{{opacity:0}},{total - .5:.3f});tl.set("#k-p-{fim}",{{opacity:1}},{total - .5:.3f});')
    for i in range(int(total / 1.6)):
        js.append(f'tl.to("#k-stage",{{scaleY:1.012,duration:.8,ease:"sine.inOut",{O}}},{i * 1.6:.2f});')
        js.append(f'tl.to("#k-stage",{{scaleY:1,duration:.8,ease:"sine.inOut",{O}}},{i * 1.6 + .8:.2f});')
    rnd, tb = random.Random(7), 1.2
    while tb < total - .3:
        js.append(f'tl.set(".lids",{{opacity:1}},{tb:.2f});tl.set(".lids",{{opacity:0}},{tb + .1:.2f});')
        tb += 2.2 + rnd.random() * 2.2
    js.append('tl.fromTo("#hookin",{scale:1},{scale:1.04,duration:.6,yoyo:true,repeat:3,ease:"sine.inOut"},0);')

    palco = mascote_rig.html(raiz, os.path.join(proj, "assets"), pose_inicial=segs[0].get("pose"))
    doc = f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="UTF-8" /><meta name="viewport" content="width={W}, height={H}" />
<script src="assets/gsap.min.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:{fundo}; }}
  #root {{ width:100%; height:100%; position:relative; font-family:Montserrat, sans-serif; }}
  #bg {{ position:absolute; inset:0; background:radial-gradient(circle at 50% 45%, #ffffff55 0%, {fundo} 55%, {fundo} 100%); }}
  #cam {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; transform-origin:540px 900px; }}
  #hook {{ position:absolute; left:70px; right:70px; top:180px; text-align:center; }}
  #hookin {{ display:inline-block; background:#1d1715; color:#fff; font-weight:900; font-size:78px; line-height:1.1;
            padding:22px 34px; border-radius:26px; box-shadow:0 10px 0 {dest}; }}
  .cap {{ position:absolute; left:60px; right:60px; top:1290px; text-align:center; }}
  .capin {{ display:inline-block; font-weight:900; font-size:92px; line-height:1.05; text-transform:uppercase; color:#fff;
           -webkit-text-stroke:14px #1d1715; paint-order:stroke fill; letter-spacing:-1px; }}
  .k-pose img {{ filter: drop-shadow(0 18px 22px rgba(0,0,0,.25)); }}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="{W}" data-height="{H}">
  <div id="bg" class="clip" data-start="0" data-duration="{total:.3f}" data-track-index="0"></div>
  <div id="stage" class="clip" data-start="0" data-duration="{total:.3f}" data-track-index="1" data-layout-allow-overflow>
    <div id="cam">{palco}</div>
  </div>
  <div id="hook" class="clip" data-start="0" data-duration="{total:.3f}" data-track-index="2"><div id="hookin">{html.escape(rot.get("hook", ""))}</div></div>
  <div id="caps" class="clip" data-start="0" data-duration="{total:.3f}" data-track-index="3" data-track-kind="captions">{"".join(caps)}</div>
  <audio id="voz" src="assets/voz.wav" data-start="0" data-volume="1"></audio>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
tl.set({{}}, {{}}, {total:.3f});
window.__timelines["main"] = tl;
</script></body></html>'''
    open(os.path.join(proj, "index.html"), "w").write(doc)
    json.dump({"paths": {"assets": "assets"}}, open(os.path.join(proj, "hyperframes.json"), "w"))
    ps = pausas(full)
    print(f"[voz] {modo} | pausas encurtadas {cortes} | pausas finais {ps} (maior {max(ps) if ps else 0}s)")
    print(f"[projeto] {proj} | {total:.2f}s | {len(cues)} bocas | {len(pags)} legendas")
    if "--sem-render" in sys.argv:
        return
    saida = os.path.join(os.path.dirname(os.path.abspath(raiz)), "saida", nome + ".mp4")
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    subprocess.run(["npx", "hyperframes", "render", "-o", saida, "--fps", str(FPS)], cwd=proj, check=True,
                   capture_output=True, text=True)
    print("[video]", saida)


if __name__ == "__main__":
    main()
```
