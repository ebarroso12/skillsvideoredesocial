#!/usr/bin/env python3
"""Gera artes de teste (linhas pretas em fundo branco) para validar o motor sem usar gerador de imagem."""
import math, random, sys
from pathlib import Path
from PIL import Image, ImageDraw

def person(path, seed=1):
    random.seed(seed)
    W, H = 1400, 1500
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    lw = 9
    d.ellipse([480, 120, 920, 620], outline="black", width=lw)                 # cabeca
    d.arc([560, 330, 840, 520], 20, 160, fill="black", width=lw)               # sorriso triste invertido
    d.ellipse([590, 300, 640, 350], outline="black", width=lw); d.ellipse([760, 300, 810, 350], outline="black", width=lw)
    d.line([560, 270, 650, 255], fill="black", width=lw); d.line([750, 255, 840, 270], fill="black", width=lw)
    d.line([700, 340, 690, 420, 715, 425], fill="black", width=lw)             # nariz
    d.arc([440, 60, 960, 420], 190, 350, fill="black", width=lw)               # cabelo
    for i in range(14):                                                        # fios de cabelo
        x = 500 + i * 30; d.line([x, 150, x - 10, 95], fill="black", width=6)
    d.line([700, 620, 700, 700], fill="black", width=lw)                       # pescoco
    d.polygon([(520, 700), (880, 700), (1010, 1100), (390, 1100)], outline="black", width=lw)  # tronco
    d.line([520, 700, 330, 1000], fill="black", width=lw); d.line([880, 700, 1070, 1000], fill="black", width=lw)  # bracos
    d.ellipse([290, 990, 380, 1080], outline="black", width=lw); d.ellipse([1020, 990, 1110, 1080], outline="black", width=lw)
    for k in range(30):                                                        # hachura na roupa
        x = 420 + k * 20; d.line([x, 900 + (k % 3) * 8, x + 70, 1090], fill="black", width=4)
    # correntes
    for cx, cy in [(330, 1080), (1070, 1080), (700, 1160)]:
        for j in range(5):
            d.ellipse([cx - 40 + j * 4, cy + j * 52, cx + 40 + j * 4, cy + 44 + j * 52], outline="black", width=7)
    d.line([300, 1400, 1100, 1400], fill="black", width=lw)
    for k in range(40):
        x = 310 + k * 20; d.line([x, 1405, x - 20, 1450], fill="black", width=4)
    im.save(path)

if __name__ == "__main__":
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    person(out / "pessoa.png", 1)
    print("ok", out)
