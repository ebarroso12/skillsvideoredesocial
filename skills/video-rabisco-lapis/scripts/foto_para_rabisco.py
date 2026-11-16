#!/usr/bin/env python3
"""
foto_para_rabisco.py - transforma uma FOTO em arte de linhas preto e branco (estilo rabisco de marcador),
pronta para o build_sketch_video.py desenhar na tela. Funciona 100% offline (OpenCV), sem gerador de
imagem e sem custo.

Uso:
  python3 foto_para_rabisco.py foto.jpg saida.png                 # contorno limpo
  python3 foto_para_rabisco.py foto.jpg saida.png --hachura       # + sombreado em tracos diagonais
  python3 foto_para_rabisco.py foto.jpg saida.png --detalhe 0.6   # 0.3 (so o essencial) .. 1.0 (detalhado)

Dica: para caricatura de verdade (rosto exagerado, expressivo) use um gerador de imagem com o prompt de
references/prompts-rabisco.md e, se quiser, passe o resultado por este script para limpar os tracos.
Sempre use so fotos que a propria pessoa enviou.
"""
import argparse
import sys

import cv2
import numpy as np


def sketch(src, detail=0.6, hatch=False, max_side=1600):
    img = cv2.imread(str(src), cv2.IMREAD_COLOR)
    if img is None:
        sys.exit(f"Nao consegui abrir a imagem: {src}")
    h, w = img.shape[:2]
    k = max_side / max(h, w)
    if k < 1:
        img = cv2.resize(img, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.bilateralFilter(g, 9, 55, 55).astype(np.float32) / 255.0
    sig = 1.2 + (1.0 - detail) * 2.6                      # menos detalhe -> sigma maior
    a = cv2.GaussianBlur(g, (0, 0), sig)
    b = cv2.GaussianBlur(g, (0, 0), sig * 1.6)
    xd = a - 0.98 * b                                      # XDoG
    eps, phi = -0.012 - (1 - detail) * 0.01, 28.0
    out = np.where(xd >= eps, 1.0, 1.0 + np.tanh(phi * (xd - eps)))
    ink = (out < 0.5).astype(np.uint8)
    # reforco: bordas de Canny (pega contornos de regioes de cor chapada, onde o XDoG falha)
    g8 = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (0, 0), 1.6)
    lo = int(40 + (1 - detail) * 40)
    ink = np.maximum(ink, (cv2.Canny(g8, lo, lo * 2.5) > 0).astype(np.uint8))
    if hatch:
        dark = (cv2.GaussianBlur(g, (0, 0), 3) < 0.30).astype(np.uint8)
        yy, xx = np.mgrid[0:ink.shape[0], 0:ink.shape[1]]
        lines = (((xx + yy) % 11) < 2).astype(np.uint8)
        ink = np.maximum(ink, dark * lines)
    # limpa pontinhos e engrossa para traco de marcador
    n, lab, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    keep = np.zeros(n, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= max(30, int(0.00004 * ink.size))
    ink = keep[lab].astype(np.uint8)
    ink = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    return (255 - ink * 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(description="Foto -> arte de linhas preto e branco (rabisco).")
    ap.add_argument("foto")
    ap.add_argument("saida")
    ap.add_argument("--detalhe", type=float, default=0.6, help="0.3 a 1.0 (padrao 0.6)")
    ap.add_argument("--hachura", action="store_true", help="adiciona sombreado em tracos diagonais")
    a = ap.parse_args()
    cv2.imwrite(a.saida, sketch(a.foto, min(max(a.detalhe, 0.2), 1.0), a.hachura))
    print("ok:", a.saida)


if __name__ == "__main__":
    main()
