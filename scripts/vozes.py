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
