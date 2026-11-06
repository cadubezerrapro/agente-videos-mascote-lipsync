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
