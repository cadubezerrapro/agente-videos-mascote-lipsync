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
