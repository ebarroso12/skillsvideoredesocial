#!/usr/bin/env python3
"""Gera os sprites da ferramenta de desenho (mao+marcador e lapis) em escala de cinza. Saida: assets/*.png + sprites.json"""
import json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np

SS = 2  # supersample

def rot_poly(cx, cy, pts, ang):
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]

def shade(layer_mask, base=170, hi=225, lo=95, light=(-1, -1)):
    """Cor com gradiente suave + sombra interna, a partir de uma mascara L."""
    m = np.array(layer_mask).astype(np.float32) / 255
    b = np.array(layer_mask.filter(ImageFilter.GaussianBlur(14 * SS / 4))).astype(np.float32) / 255
    # b menor perto da borda: escurece bordas (volume)
    edge = np.clip(1 - b, 0, 1) * m
    gy, gx = np.gradient(np.array(layer_mask.filter(ImageFilter.GaussianBlur(10 * SS / 4))).astype(np.float32) / 255)
    lit = np.clip((gx * light[0] + gy * light[1]) * -8, -1, 1)
    val = base + lit * (hi - base) * (lit > 0) + lit * (base - lo) * (lit < 0) - edge * 55
    return Image.fromarray(np.clip(val, 0, 255).astype(np.uint8), "L")

OFFY = 0

def _capsule(dr, pts_r, fill=255):
    pts_r = [(x, y + OFFY, r) for x, y, r in pts_r]
    for (x0, y0, r0), (x1, y1, r1) in zip(pts_r[:-1], pts_r[1:]):
        n = 30
        for i in range(n + 1):
            t = i / n
            x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t; r = r0 + (r1 - r0) * t
            dr.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=fill)

def _part(canvas, mask, fill=228, line=28, lw=3.2, shade_amt=34):
    """Aplica uma parte com contorno de tinta e leve sombreado interno (estilo ilustracao)."""
    mask = mask.filter(ImageFilter.GaussianBlur(0.8 * SS))
    outline = mask.filter(ImageFilter.MaxFilter(int(lw * SS) * 2 + 1))
    canvas = Image.composite(Image.new("L", canvas.size, line), canvas, outline)
    inner = np.array(mask.filter(ImageFilter.GaussianBlur(9 * SS))).astype(np.float32) / 255
    val = fill - (1 - inner) * shade_amt
    # sombra na parte de baixo/direita
    gy = np.gradient(np.array(mask.filter(ImageFilter.GaussianBlur(16 * SS))).astype(np.float32) / 255, axis=0)
    val = val + np.clip(gy * 140, -18, 0)
    body = Image.fromarray(np.clip(val, 0, 255).astype(np.uint8), "L")
    return Image.composite(body, canvas, mask.point(lambda v: 255 if v > 127 else 0))

def build_hand(W=1500, H=1000, ang_deg=24, tool='marcador'):
    global OFFY
    OFFY = 520
    w, h = W * SS, H * SS
    ang = math.radians(ang_deg)
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    tip = (44 * SS, (92 + OFFY) * SS)
    L = 340 * SS; wd = 30 * SS
    canvas = Image.new("L", (w, h), 0)      # tons de cinza
    alpha = Image.new("L", (w, h), 0)       # silhueta total

    def new_mask(): 
        m = Image.new("L", (w, h), 0); return m, ImageDraw.Draw(m)
    # 1) antebraco afunilado saindo pelo canto superior direito (manga ao fundo)
    m, d = new_mask()
    _capsule(d, [(395, 150, 66), (520, 95, 74), (640, 40, 84), (760, -20, 100), (1100, -200, 120), (1700, -560, 150)])
    canvas = _part(canvas, m, fill=226); alpha = ImageChops.lighter(alpha, m.filter(ImageFilter.MaxFilter(9)))
    m, d = new_mask()
    _capsule(d, [(590, 62, 86), (1700, -560, 190)])          # manga
    canvas = _part(canvas, m, fill=205, shade_amt=40); alpha = ImageChops.lighter(alpha, m.filter(ImageFilter.MaxFilter(9)))
    # 2) dorso da mao
    m, d = new_mask()
    _capsule(d, [(400, 140, 70), (330, 175, 78)])
    canvas = _part(canvas, m, fill=232); alpha = ImageChops.lighter(alpha, m.filter(ImageFilter.MaxFilter(9)))
    # 3) dedos curvados (anelar, minimo, medio) por tras do marcador
    for pts in ([(335, 215, 30), (300, 270, 27), (262, 292, 22)],
                [(375, 200, 28), (352, 262, 26), (322, 292, 21)],
                [(300, 150, 30), (230, 190, 27), (196, 205, 22)]):
        m, d = new_mask(); _capsule(d, pts)
        canvas = _part(canvas, m, fill=226); alpha = ImageChops.lighter(alpha, m.filter(ImageFilter.MaxFilter(9)))
    # 4) marcador
    mk, dm = new_mask()
    a = (tip[0] + ux * 44 * SS, tip[1] + uy * 44 * SS); b = (tip[0] + ux * L, tip[1] + uy * L)
    dm.polygon([tip, (a[0] + nx * wd * 0.45, a[1] + ny * wd * 0.45), (a[0] - nx * wd * 0.45, a[1] - ny * wd * 0.45)], fill=255)
    dm.polygon([(a[0] + nx * wd / 2, a[1] + ny * wd / 2), (b[0] + nx * wd / 2, b[1] + ny * wd / 2),
                (b[0] - nx * wd / 2, b[1] - ny * wd / 2), (a[0] - nx * wd / 2, a[1] - ny * wd / 2)], fill=255)
    dm.ellipse([b[0] - wd / 2, b[1] - wd / 2, b[0] + wd / 2, b[1] + wd / 2], fill=255)
    mk_s = mk.filter(ImageFilter.GaussianBlur(0.7 * SS))
    body_val = 20 if tool == 'marcador' else 150
    canvas = Image.composite(Image.new("L", (w, h), body_val), canvas, mk_s.point(lambda v: 255 if v > 127 else 0))
    hl = Image.new("L", (w, h), 0); dh = ImageDraw.Draw(hl)
    dh.line([(a[0] + nx * wd * 0.2, a[1] + ny * wd * 0.2), (b[0] + nx * wd * 0.2, b[1] + ny * wd * 0.2)], fill=150, width=int(4 * SS))
    hl = hl.filter(ImageFilter.GaussianBlur(1.6 * SS))
    canvas = ImageChops.add(canvas, ImageChops.multiply(hl, mk_s.point(lambda v: 255 if v > 127 else 0)))
    alpha = ImageChops.lighter(alpha, mk_s.filter(ImageFilter.MaxFilter(5)))
    # 5) polegar (por baixo do marcador, apertando) e indicador (por cima)
    for pts in ([(330, 195, 33), (250, 172, 26), (190, 150, 20)],      # polegar
                [(318, 112, 34), (240, 112, 27), (172, 112, 22), (150, 113, 19)]):  # indicador
        m, d = new_mask(); _capsule(d, pts)
        canvas = _part(canvas, m, fill=236); alpha = ImageChops.lighter(alpha, m.filter(ImageFilter.MaxFilter(9)))
        # unha
        tx, ty, r = pts[-1]; ty += OFFY
        dn = ImageDraw.Draw(canvas)
        dn.ellipse([(tx - r * 0.55 - 2) * SS, (ty - r * 0.55) * SS, (tx + r * 0.2) * SS, (ty + r * 0.45) * SS], outline=70, width=int(2 * SS))
    # sombra projetada no papel
    shadow = alpha.filter(ImageFilter.GaussianBlur(12 * SS)).point(lambda v: int(v * 0.30))
    sh = Image.new("L", (w, h), 0); sh.paste(shadow, (14 * SS, 20 * SS))
    rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh_rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sh_rgba.putalpha(sh)
    rgba = Image.alpha_composite(rgba, sh_rgba)
    hand_rgba = Image.merge("RGBA", (canvas, canvas, canvas, alpha.point(lambda v: 255 if v > 20 else 0)))
    rgba = Image.alpha_composite(rgba, hand_rgba)
    return rgba.resize((W, H), Image.LANCZOS), (tip[0] // SS, tip[1] // SS)

def build_pencil(W=640, H=400, ang_deg=-38):
    w, h = W * SS, H * SS
    ang = math.radians(ang_deg)
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    tip = (30 * SS, 372 * SS)   # lapis sobe para a direita
    L = 440 * SS; wd = 34 * SS
    m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
    a = (tip[0] + ux * 70 * SS, tip[1] + uy * 70 * SS); b = (tip[0] + ux * L, tip[1] + uy * L)
    d.polygon([tip, (a[0] + nx * wd / 2, a[1] + ny * wd / 2), (a[0] - nx * wd / 2, a[1] - ny * wd / 2)], fill=255)
    d.polygon([(a[0] + nx * wd / 2, a[1] + ny * wd / 2), (b[0] + nx * wd / 2, b[1] + ny * wd / 2),
               (b[0] - nx * wd / 2, b[1] - ny * wd / 2), (a[0] - nx * wd / 2, a[1] - ny * wd / 2)], fill=255)
    base = shade(m.filter(ImageFilter.GaussianBlur(0.6 * SS)), base=120, hi=190, lo=45)
    arr = np.array(base).astype(np.float32)
    # madeira do cone mais clara, grafite escuro na ponta, faixa de borracha
    yy, xx = np.mgrid[0:h, 0:w]
    t = ((xx - tip[0]) * ux + (yy - tip[1]) * uy) / SS
    arr = np.where((t < 70) & (t >= 0), arr * 0 + 205, arr)
    arr = np.where((t < 20) & (t >= 0), 35, arr)
    arr = np.where((t > 420), 215, arr)
    arr = np.where((t > 400) & (t <= 420), 80, arr)
    base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L")
    sh = m.filter(ImageFilter.GaussianBlur(9 * SS)).point(lambda v: int(v * 0.3))
    rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh_rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sh_rgba.putalpha(sh)
    shw = Image.new("RGBA", (w, h), (0, 0, 0, 0)); shw.paste(sh_rgba, (12 * SS, 16 * SS)); rgba = Image.alpha_composite(rgba, shw)
    rgba = Image.alpha_composite(rgba, Image.merge("RGBA", (base, base, base, m)))
    return rgba.resize((W, H), Image.LANCZOS), (tip[0] // SS, tip[1] // SS)

if __name__ == "__main__":
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    meta = {}
    for name, fn in [("mao-marcador", lambda: build_hand(tool='marcador')), ("mao-lapis", lambda: build_hand(tool='lapis')),
                     ("lapis", build_pencil)]:
        img, tip = fn(); img.save(out / f"{name}.png"); meta[name] = {"ponta": list(tip), "tamanho": list(img.size)}
    (out / "sprites.json").write_text(json.dumps(meta, indent=2))
    print(meta)
