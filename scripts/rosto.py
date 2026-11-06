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
