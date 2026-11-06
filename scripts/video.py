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
