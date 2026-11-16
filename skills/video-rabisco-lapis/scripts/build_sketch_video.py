#!/usr/bin/env python3
"""
build_sketch_video.py - video vertical (9:16, ate 60 s) em que um RABISCO preto e branco
e desenhado na tela por uma mao com marcador/lapis, traco a traco, sobre papel.

Entrada : project.json (ver templates/project.example.json). Cada cena pode ter:
            "imagem"  : arte em linhas (preto no branco / PNG transparente) -> e desenhada
            "escrever": texto escrito a mao (frase, numero, versiculo)
            "texto"   : fala/legenda da cena (vira legenda queimada e define o tempo)
Saida   : MP4 1080x1920 30 fps (H.264 + AAC) + legenda.txt do post (se "post" no project).

Como o movimento do lapis e feito (e por que fica convincente):
  1. a arte vira "esqueleto" (linha central de cada traco);
  2. os tracos sao ordenados como um artista faria (contornos grandes primeiro, depois detalhes;
     texto na ordem de leitura) e percorridos pixel a pixel, sem saltos;
  3. cada pixel de tinta aparece exatamente quando a ponta passa por perto (sincronia perfeita);
  4. a velocidade acelera/desacelera em cada traco, a mao entra, levanta entre tracos (arco),
     treme levemente e sai no fim; um chiado de marcador acompanha so quando a ponta toca o papel.
Trava de duracao: nunca entrega mais que max_segundos (60).

Dependencias: python3, numpy, scipy, scikit-image, opencv-python(-headless), Pillow, ffmpeg (libass).
"""
import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from scipy import ndimage as ndi
    from skimage.morphology import skeletonize
except ImportError as e:  # pragma: no cover
    sys.exit(f"Falta uma dependencia ({e.name}). Instale:  pip install numpy scipy scikit-image opencv-python-headless pillow")

SKILL_DIR = Path(__file__).resolve().parent.parent
FONT_DIR = SKILL_DIR / "fonts"
ASSET_DIR = SKILL_DIR / "assets"
BASE_W, BASE_H = 1080, 1920
FPS = 30
SR = 44100
WORDS_PER_SECOND = 2.6
MIN_SCENE = 3.5
FADE = 0.2
PAPER_HEX = "#EEEBE6"
FONTS = {
    "marcador": "PermanentMarker-Regular.ttf",
    "manuscrito": "Kalam-Bold.ttf",
    "pincel": "CaveatBrush-Regular.ttf",
    "caderno": "PatrickHand-Regular.ttf",
}
N8 = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]


# ----------------------------------------------------------------------------- utils
def die(msg, code=1):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(code)


def need(binary):
    if not shutil.which(binary):
        die(f"'{binary}' nao encontrado. Instale o ffmpeg (https://ffmpeg.org/download.html).")


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        die(f"ffmpeg falhou:\n" + "\n".join(r.stderr.strip().splitlines()[-12:]))
    return r


def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        die(f"Nao consegui ler a duracao de {path}")


def count_words(t):
    return len(re.findall(r"\S+", t or ""))


def ass_time(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int((t % 3600) // 60):02d}:{t % 60:05.2f}"


def ease_io(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def ease_out(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 3


# ----------------------------------------------------------------------------- papel
def make_paper(W, H, seed=7):
    rng = np.random.default_rng(seed)
    base = np.full((H, W), 243.0, np.float32)
    low = cv2.resize(rng.normal(0, 1, (H // 90 + 3, W // 90 + 3)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * 2.4
    mid = cv2.resize(rng.normal(0, 1, (H // 9 + 3, W // 9 + 3)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * 1.3
    grain = rng.normal(0, 1.5, (H, W)).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vig = 1 - 0.13 * np.clip(r - 0.45, 0, 1.2) ** 1.7
    g = (base + low + mid + grain) * vig
    paper = np.stack([g, g, g * 0.992], -1)
    return np.clip(paper, 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------- camadas de tinta
def _font(key_or_file, size):
    f = FONTS.get(key_or_file, key_or_file)
    p = FONT_DIR / f
    if not p.exists():
        die(f"Fonte nao encontrada: {p}")
    return ImageFont.truetype(str(p), size)


def wrap_lines(draw, text, font, max_w):
    out = []
    for para in str(text).split("\n"):
        cur = ""
        for w in para.split():
            test = (cur + " " + w).strip()
            if draw.textlength(test, font=font) <= max_w or not cur:
                cur = test
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out


def layer_text(text, box, W, H, s, font_key="marcador", size=None, valign="center", align="center"):
    """Texto manuscrito dentro de box (coords base 1080x1920). Devolve (darkness HxW, line_boxes)."""
    x0, y0, x1, y1 = [v * s for v in box]
    bw, bh = x1 - x0, y1 - y0
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    size = (size or 120) * s
    while True:
        font = _font(font_key, int(size))
        lines = wrap_lines(d, text, font, bw)
        lh = font.size * 1.22
        widest = max(d.textlength(l, font=font) for l in lines)
        if (len(lines) * lh <= bh and widest <= bw) or size <= 28 * s:
            break
        size *= 0.93
    total = len(lines) * lh
    y = y0 + (bh - total) / 2 if valign == "center" else y0
    boxes = []
    for l in lines:
        w = d.textlength(l, font=font)
        x = x0 + (bw - w) / 2 if align == "center" else x0
        d.text((x, y), l, font=font, fill=255)
        boxes.append((y, y + lh))
        y += lh
    return np.asarray(img, np.float32) / 255.0, boxes


def layer_image(path, box, W, H, s):
    """Arte em linhas -> mapa de escuridao 0..1 dentro de box."""
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        im = bg
    g = np.asarray(im.convert("L"), np.float32)
    bgv = float(np.percentile(g, 92))
    dark = np.clip((bgv - g) / max(bgv - 25.0, 60.0), 0, 1)
    x0, y0, x1, y1 = [v * s for v in box]
    bw, bh = x1 - x0, y1 - y0
    k = min(bw / dark.shape[1], bh / dark.shape[0])
    nw, nh = max(1, int(dark.shape[1] * k)), max(1, int(dark.shape[0] * k))
    dark = cv2.resize(dark, (nw, nh), interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)
    out = np.zeros((H, W), np.float32)
    ox, oy = int(x0 + (bw - nw) / 2), int(y0 + (bh - nh) / 2)
    out[oy:oy + nh, ox:ox + nw] = dark
    return out


def wobble(D, s, seed=3, amp=1.4):
    """Leve tremor de mao: desloca a linha por um campo suave (nao some com o traco)."""
    H, W = D.shape
    rng = np.random.default_rng(seed)
    def field():
        f = cv2.resize(rng.normal(0, 1, (H // 38 + 3, W // 38 + 3)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        return f * amp * s
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return cv2.remap(D, xx + field(), yy + field(), cv2.INTER_LINEAR, borderValue=0)


def thicken_to_marker(D, s, target=5.0):
    """Garante um traco de marcador legivel: se a linha for fina demais, engrossa."""
    bw = D > 0.45
    if bw.sum() < 20:
        return D
    sk = skeletonize(bw)
    edt = ndi.distance_transform_edt(bw)
    vals = edt[sk]
    if vals.size == 0:
        return D
    width = 2 * float(np.median(vals))
    want = target * s
    if width < want - 0.8:
        it = int(math.ceil((want - width) / 2))
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        D = cv2.dilate(D, k, iterations=it)
    return D


# ----------------------------------------------------------------------------- tracos -> caminho da caneta
def _components(skel):
    n, lab = cv2.connectedComponents(skel.astype(np.uint8), connectivity=8)
    ys, xs = np.nonzero(skel)
    ids = lab[ys, xs]
    order = np.argsort(ids, kind="stable")
    ys, xs, ids = ys[order], xs[order], ids[order]
    cuts = np.flatnonzero(np.diff(ids)) + 1
    return [(g_y, g_x) for g_y, g_x in zip(np.split(ys, cuts), np.split(xs, cuts))]


def _walk(pix_ids, start, Wd):
    """Percurso em profundidade preferindo seguir reto (cada traco sai continuo)."""
    visited, stack, out = set(), [start], []
    last = None
    while stack:
        p = stack.pop()
        if p in visited:
            continue
        visited.add(p)
        out.append(p)
        y, x = divmod(p, Wd)
        nb = []
        for dy, dx in N8:
            q = (y + dy) * Wd + x + dx
            if q in pix_ids and q not in visited:
                nb.append((dy, dx, q))
        if len(out) >= 2:
            py, px = divmod(out[-2], Wd)
            ly, lx = y - py, x - px
        else:
            ly, lx = 0, 0
        nb.sort(key=lambda t: (t[0] * ly + t[1] * lx) - (0.01 if t[0] and t[1] else 0))
        stack.extend(q for _, _, q in nb)   # o melhor (maior produto) fica no topo
    return out


def trace_paths(skel, mode, line_boxes, start_pos):
    """Retorna lista de caminhos [(xs, ys, comp_id)] na ordem em que serao desenhados."""
    H, W = skel.shape
    comps = _components(skel)
    if len(comps) > 1500:
        comps = [c for c in comps if len(c[0]) >= 8]
    if not comps:
        return []
    info = []
    for ys, xs in comps:
        ids = set((ys * W + xs).tolist())
        deg = {}
        ends = []
        for p in ids:
            y, x = divmod(p, W)
            c = sum(1 for dy, dx in N8 if (y + dy) * W + x + dx in ids)
            if c == 1:
                ends.append(p)
        info.append({"ids": ids, "ends": ends, "n": len(ids), "cy": float(ys.mean()), "xmin": float(xs.min()),
                     "pts": np.stack([xs, ys], 1)})
    remaining = list(range(len(info)))
    seq = []
    pen = np.array(start_pos, np.float32)

    def line_index(cy):
        if not line_boxes:
            return 0
        best, bd = 0, 1e18
        for i, (a, b) in enumerate(line_boxes):
            d = 0 if a <= cy <= b else min(abs(cy - a), abs(cy - b))
            if d < bd:
                best, bd = i, d
        return best

    if mode == "leitura":
        remaining.sort(key=lambda i: (line_index(info[i]["cy"]), info[i]["xmin"]))
        pick_order = remaining
    else:
        biggest = max(c["n"] for c in info)
        outline = [i for i in remaining if info[i]["n"] >= 0.15 * biggest]
        detail = [i for i in remaining if i not in set(outline)]
        pick_order = []
        top_first = min(outline or remaining, key=lambda i: info[i]["pts"][:, 1].min())
        if top_first in outline:
            outline.remove(top_first)
            outline.insert(0, top_first)
            pen = info[top_first]["pts"][np.argmin(info[top_first]["pts"][:, 1])].astype(np.float32)
        pick_order.append(top_first)
        if top_first in outline:
            outline.remove(top_first)
        for group in (outline, detail):
            group = list(group)
            while group:
                best, bd = None, 1e18
                for i in group:
                    pts = info[i]["pts"]
                    if len(pts) > 60:
                        pts = pts[:: max(len(pts) // 60, 1)]
                    d = float(np.min(np.hypot(pts[:, 0] - pen[0], pts[:, 1] - pen[1])))
                    if d < bd:
                        best, bd = i, d
                pick_order.append(best)
                group.remove(best)
                # pen aproximado: fim do componente escolhido
                pen = info[best]["pts"][-1].astype(np.float32)
    for i in pick_order:
        c = info[i]
        starts = c["ends"] or [next(iter(c["ids"]))]
        if mode == "leitura":
            start = min(starts, key=lambda p: (divmod(p, W)[0], divmod(p, W)[1]))
        else:
            start = min(starts, key=lambda p: math.hypot(divmod(p, W)[1] - pen[0], divmod(p, W)[0] - pen[1]))
        walk = _walk(c["ids"], start, W)
        arr = np.array([(p % W, p // W) for p in walk], np.float32)
        pen = arr[-1]
        seq.append(arr)
    return seq


def build_timeline(seqs, draw_dur, s):
    """Posicoes + tempos de cada ponto; marca inicio de cada traco e saltos (caneta levantada)."""
    P, lift, u_in = [], [], []
    for arr in seqs:
        n = len(arr)
        P.append(arr)
        l = np.zeros(n, bool)
        l[0] = True
        if n > 1:
            gaps = np.hypot(*(arr[1:] - arr[:-1]).T) > 2.6 * max(s, 0.5)
            l[1:] = gaps
        lift.append(l)
        u_in.append(np.linspace(0, 1, n))
    P = np.concatenate(P)
    lift = np.concatenate(lift)
    u = np.concatenate(u_in)
    n = len(P)
    cost = np.zeros(n, np.float64)
    seg = np.zeros(n)
    seg[1:] = np.hypot(*(P[1:] - P[:-1]).T)
    ease = 0.55 + 0.45 * np.sin(np.pi * np.clip(u, 0.02, 0.98))
    cost[:] = 1.0 / ease
    lifts = np.flatnonzero(lift)
    cost[lifts] = 7.0 + seg[lifts] / 4.5          # levantar, deslocar e baixar
    cost[0] = 0.0
    cum = np.cumsum(cost)
    # velocidade maxima de desenho: nao arrastar traco simples demais
    vmin = 230.0 * s
    drawn_px = float((~lift).sum())
    dur = min(draw_dur, max(cum[-1] / vmin * 1.0, 0.8))
    times = cum / cum[-1] * dur
    return P, times, lift, dur, drawn_px


# ----------------------------------------------------------------------------- sprites
def load_sprite(name, scale):
    meta = json.loads((ASSET_DIR / "sprites.json").read_text())[name]
    im = Image.open(ASSET_DIR / f"{name}.png").convert("RGBA")
    w, h = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    im = im.resize((w, h), Image.LANCZOS)
    arr = np.asarray(im, np.float32)
    return arr[..., :3], arr[..., 3:4] / 255.0, (meta["ponta"][0] * scale, meta["ponta"][1] * scale)


def paste_sprite(frame, rgb, a, tip, pos):
    H, W = frame.shape[:2]
    x0 = int(round(pos[0] - tip[0]))
    y0 = int(round(pos[1] - tip[1]))
    h, w = a.shape[:2]
    sx0, sy0 = max(0, -x0), max(0, -y0)
    ex0, ey0 = max(0, x0), max(0, y0)
    ex1, ey1 = min(W, x0 + w), min(H, y0 + h)
    if ex1 <= ex0 or ey1 <= ey0:
        return
    sw, sh = ex1 - ex0, ey1 - ey0
    reg = frame[ey0:ey1, ex0:ex1].astype(np.float32)
    aa = a[sy0:sy0 + sh, sx0:sx0 + sw]
    rr = rgb[sy0:sy0 + sh, sx0:sx0 + sw]
    frame[ey0:ey1, ex0:ex1] = np.clip(reg * (1 - aa) + rr * aa, 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------- som do marcador
def pen_sound(down_env, n_samples, seed=5):
    """Chiado de marcador/lapis sobre papel: ruido filtrado, amplitude segue a caneta tocando o papel."""
    from scipy.signal import butter, sosfilt
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 1, n_samples)
    sos = butter(2, [1800, 7500], btype="band", fs=SR, output="sos")
    sig = sosfilt(sos, noise)
    t_frames = np.arange(len(down_env)) / FPS
    env = np.interp(np.arange(n_samples) / SR, t_frames, down_env)
    env = np.convolve(env, np.ones(int(SR * 0.012)) / int(SR * 0.012), mode="same")
    wob = 0.75 + 0.25 * np.sin(2 * np.pi * 9 * np.arange(n_samples) / SR + rng.uniform(0, 6))
    sig = sig * env * wob
    peak = float(np.max(np.abs(sig))) or 1.0
    return (sig / peak * 0.5).astype(np.float32)


# ----------------------------------------------------------------------------- legenda
WEAK_END = {"a", "o", "e", "as", "os", "um", "uma", "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
            "que", "com", "por", "para", "pra", "se", "me", "te", "ao", "à", "ou", "mas", "não", "sua", "seu", "meu", "minha"}


def chunk_text(text, max_words=3):
    words = re.findall(r"\S+", text or "")
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        base = re.sub(r"[^\wÀ-ÿ]", "", w).lower()
        punct = bool(re.search(r"[.!?;:]$", w)) or (len(cur) >= 2 and w.endswith(","))
        full = len(cur) >= max_words
        more = i + 1 < len(words)
        if punct or (full and not (base in WEAK_END and more and len(cur) < max_words + 2)):
            chunks.append(" ".join(cur))
            cur = []
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def build_ass(text, duration, cfg, y_pos):
    chunks = chunk_text(text, cfg.get("palavras_por_bloco", 3))
    size = cfg.get("tamanho", 80)
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Cap,Kalam,{size},&H00141414,&H000000FF,&H00E6EBEE,&H00000000,-1,0,0,0,100,100,0,0,1,7,0,5,90,90,0,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    if not chunks:
        return header
    start0, end_all = 0.3, max(duration - 0.3, 0.8)
    weights = [len(c) + 2 for c in chunks]
    total = sum(weights)
    t, lines = start0, []
    for c, wgt in zip(chunks, weights):
        d = (end_all - start0) * wgt / total
        lines.append(f"Dialogue: 0,{ass_time(t)},{ass_time(t + d)},Cap,,0,0,0,,{{\\an5\\pos(540,{y_pos})\\fad(100,60)}}"
                     + c.replace("{", "(").replace("}", ")"))
        t += d
    return header + "\n".join(lines) + "\n"


# ----------------------------------------------------------------------------- tela final (CTA)
def render_cta(dst, brand, cta_cfg, W, H, s):
    paper = Image.fromarray(make_paper(W, H, seed=11))
    d = ImageDraw.Draw(paper)
    ink = (24, 24, 26)
    cx = W // 2
    y = 230 * s
    logo_p = SKILL_DIR / "brand" / "logos" / "logo-vertical-preta.png"
    if logo_p.exists():
        lg = Image.open(logo_p).convert("RGBA")
        lw = int(520 * s)
        lh = int(lg.height * lw / lg.width)
        lg = lg.resize((lw, lh), Image.LANCZOS)
        paper.paste(lg, ((W - lw) // 2, int(y)), lg)
        y += lh + 90 * s

    def center(text, font, fill, y, max_w=900 * s, gap=10 * s):
        for l in wrap_lines(d, text, font, max_w):
            w = d.textlength(l, font=font)
            d.text((cx - w / 2, y), l, font=font, fill=fill)
            y += font.size * 1.15 + gap
        return y

    y = center(cta_cfg.get("titulo", "Agende sua consulta"), _font("marcador", int(92 * s)), ink, y)
    y = center(cta_cfg.get("subtitulo", "e dê o primeiro passo para cuidar de você"), _font("manuscrito", int(44 * s)), (60, 60, 62), y + 8 * s)
    y += 36 * s
    d.line([(cx - 110 * s, y), (cx + 110 * s, y)], fill=ink, width=max(2, int(4 * s)))
    y += 54 * s
    y = center(f"WhatsApp  {brand['whatsapp']}", _font("marcador", int(54 * s)), ink, y)
    y += 24 * s
    for l in brand.get("endereco", []):
        y = center(l, _font("caderno", int(40 * s)), (40, 40, 42), y, gap=4 * s)
    y += 30 * s
    y = center(brand["site"], _font("marcador", int(46 * s)), ink, y)
    if brand.get("instagram"):
        y = center(brand["instagram"], _font("manuscrito", int(40 * s)), (60, 60, 62), y)
    if brand.get("registro_profissional"):
        sm = _font("caderno", int(30 * s))
        txt = f"{brand['nome']} · {brand['registro_profissional']}"
        d.text((cx - d.textlength(txt, font=sm) / 2, H - 150 * s), txt, font=sm, fill=(90, 90, 92))
    paper.save(dst, "PNG")


def write_post_caption(dst, post, brand):
    corpo = (post.get("corpo") or "").strip()
    hashtags = post.get("hashtags") or brand.get("hashtags_base", [])
    partes = [corpo] if corpo else []
    if post.get("incluir_cta", True):
        bloco = [brand.get("cta_frase", "Agende sua consulta."), "", f"WhatsApp: {brand['whatsapp']}", ""]
        bloco += brand.get("endereco", []) + ["", brand["site"]]
        reg = " — ".join(x for x in [brand.get("nome"), brand.get("registro_profissional")] if x)
        if reg:
            bloco.append(reg)
        partes.append("\n".join(bloco))
    if hashtags:
        partes.append(" ".join(hashtags))
    Path(dst).write_text("\n\n".join(partes) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------- cena
def plan_layers(sc, res, W, H, s, seed):
    """Monta as camadas de tinta de uma cena. Retorna lista [(darkness, modo, line_boxes)]."""
    has_img, has_txt = bool(sc.get("imagem")), bool(sc.get("escrever"))
    if has_img and has_txt:
        tbox, ibox = (90, 150, 990, 470), (70, 500, 1010, 1380)
    elif has_txt:
        tbox, ibox = (90, 330, 990, 1280), None
    else:
        tbox, ibox = None, (70, 170, 1010, 1380)
    layers = []
    if has_txt:
        D, lines = layer_text(sc["escrever"], tbox, W, H, s, sc.get("fonte", "marcador"), sc.get("tamanho_escrita", 120),
                              valign="top" if has_img else "center")
        layers.append((wobble(D, s, seed, 0.9), "leitura", lines))
    if has_img:
        p = res(sc["imagem"])
        if not p.exists():
            die(f"Imagem nao encontrada: {sc['imagem']}")
        D = layer_image(p, ibox, W, H, s)
        D = thicken_to_marker(D, s, sc.get("espessura", 5.0))
        layers.append((wobble(D, s, seed + 1, 1.5), "proximidade", None))
    return layers


def render_scene(sc, idx, dur, W, H, s, paper, tool, ink_val, tmp, fonts_dir, wm_file, wm_w, mx, my, wm_op,
                 cap_cfg, preview, res, seed):
    layers = plan_layers(sc, res, W, H, s, seed)
    n_frames = int(round(dur * FPS))
    t_entry, t_exit, t_hold_end = 0.45, 0.55, 0.45
    draw_budget = max(dur - t_entry - t_exit - t_hold_end - 0.25, 1.0)

    # --- esqueleto e caminho
    D_all = np.zeros((H, W), np.float32)
    seqs = []
    pen = (W * 0.5, H * 0.05)
    for D, mode, lines in layers:
        D_all = np.maximum(D_all, D)
        sk = skeletonize(D > 0.45)
        sq = trace_paths(sk, mode, lines, pen)
        if sq:
            pen = tuple(sq[-1][-1])
        seqs += sq
    if not seqs:
        die(f"Cena {idx}: nada para desenhar (imagem vazia ou sem tracos escuros).")
    P, times, lift, draw_dur, drawn_px = build_timeline(seqs, draw_budget, s)
    px_s = drawn_px / max(draw_dur, 0.1) / s
    note = " (muito rapido: simplifique a arte)" if px_s > 3800 else ""
    print(f"  cena {idx:02d}: {len(seqs)} tracos, {int(drawn_px)} px, desenha em {draw_dur:.1f}s{note}")

    # --- tinta final e tempo de aparicao por pixel
    ink = np.asarray(D_all, np.float32)
    rng = np.random.default_rng(seed)
    tex = 0.9 + 0.1 * cv2.resize(rng.random((H // 3 + 2, W // 3 + 2)).astype(np.float32), (W, H))
    dd = np.clip(ink * tex, 0, 1)[..., None]
    ink_rgb = paper.astype(np.float32) * (1 - dd) + ink_val * dd
    ink_rgb = ink_rgb.astype(np.uint8)
    sk_all = np.zeros((H, W), bool)
    ix, iy = np.round(P[:, 0]).astype(int), np.round(P[:, 1]).astype(int)
    ix, iy = np.clip(ix, 0, W - 1), np.clip(iy, 0, H - 1)
    tgrid = np.full((H, W), np.inf, np.float32)
    # o pixel visitado primeiro vale (ordem reversa para o primeiro sobrescrever por ultimo)
    tgrid[iy[::-1], ix[::-1]] = times[::-1].astype(np.float32)
    sk_all[iy, ix] = True
    _, (ny, nx) = ndi.distance_transform_edt(~sk_all, return_indices=True)
    ys, xs = np.nonzero(ink > 0.04)
    treveal = tgrid[ny[ys, xs], nx[ys, xs]] - 0.02
    o = np.argsort(treveal, kind="stable")
    ys, xs, treveal = ys[o], xs[o], treveal[o]

    # --- trajetoria da ponta por quadro
    t_start = t_entry
    t_end_draw = t_start + draw_dur
    entry_pt = np.array([W * 1.05, H * 0.92])
    exit_pt = np.array([W * 1.05, H * 0.95])
    tips, down = np.zeros((n_frames, 2)), np.zeros(n_frames)
    lift_idx = np.flatnonzero(lift)
    for f in range(n_frames):
        t = f / FPS
        if t < t_start:
            u = ease_out(t / t_entry)
            tips[f] = entry_pt + (P[0] - entry_pt) * u
        elif t <= t_end_draw:
            td = t - t_start
            i = int(np.searchsorted(times, td))
            i = min(max(i, 1), len(P) - 1)
            span = max(times[i] - times[i - 1], 1e-6)
            u = (td - times[i - 1]) / span
            tips[f] = P[i - 1] + (P[i] - P[i - 1]) * u
            if lift[i]:
                tips[f, 1] -= math.sin(math.pi * min(max(u, 0), 1)) * 22 * s
            else:
                down[f] = 1.0
        else:
            u = ease_io((t - t_end_draw - 0.12) / t_exit)
            tips[f] = P[-1] + (exit_pt - P[-1]) * u
    # tremor sutil + suavizacao (movimento fluido, sem "pixel a pixel")
    ft = np.arange(n_frames) / FPS
    tips[:, 0] += 0.9 * s * (np.sin(2 * np.pi * 1.7 * ft) + 0.5 * np.sin(2 * np.pi * 4.3 * ft + 1.0))
    tips[:, 1] += 0.9 * s * (np.sin(2 * np.pi * 2.1 * ft + 0.5) + 0.5 * np.sin(2 * np.pi * 5.1 * ft))
    tips = ndi.gaussian_filter1d(tips, 1.1, axis=0, mode="nearest")

    spr_name = {"marcador": "mao-marcador", "lapis": "mao-lapis", "lapis-solto": "lapis"}[tool]
    spr_rgb, spr_a, spr_tip = load_sprite(spr_name, 0.85 * s)

    # --- ass + ffmpeg
    ass_name = f"cap_{idx:02d}.ass"
    if cap_cfg.get("ativa", True) and sc.get("texto"):
        (tmp / ass_name).write_text(build_ass(sc["texto"], min(dur, sc["_fala_dur"] + 0.7) if sc.get("_fala_dur") else dur, cap_cfg, int(cap_cfg.get("posicao_y", 1470))), encoding="utf-8")
        ass_f = f",ass={ass_name}:fontsdir=fonts"
    else:
        ass_f = ""
    fade_in = 0.15 if idx > 1 else 0.1
    paper_c = PAPER_HEX.replace("#", "0x")
    fg = (f"[0:v]format=rgba[bg];[1:v]scale={wm_w}:-1,format=rgba,colorchannelmixer=aa={wm_op}[wm];"
          f"[bg][wm]overlay=x=W-w-{mx}:y=H-h-{my}:shortest=1,format=yuv420p{ass_f},"
          f"fade=t=in:st=0:d={fade_in}:color={paper_c},fade=t=out:st={dur - FADE:.3f}:d={FADE}:color={paper_c}[v]")
    part = tmp / f"scene_{idx:02d}.part.mp4"
    final = tmp / f"scene_{idx:02d}.mp4"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-loop", "1", "-i", str(wm_file), "-filter_complex", fg, "-map", "[v]",
           "-frames:v", str(n_frames), "-an", "-c:v", "libx264", "-preset", "ultrafast" if preview else "veryfast",
           "-crf", "28" if preview else "18", "-pix_fmt", "yuv420p", "-r", str(FPS), part.name]
    proc = subprocess.Popen(cmd, cwd=tmp, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    cur = paper.copy()
    cursor = 0
    try:
        for f in range(n_frames):
            td = f / FPS - t_start
            nxt = int(np.searchsorted(treveal, td, side="right"))
            if nxt > cursor:
                cur[ys[cursor:nxt], xs[cursor:nxt]] = ink_rgb[ys[cursor:nxt], xs[cursor:nxt]]
                cursor = nxt
            frame = cur.copy() if t_start - 1e-9 <= f / FPS or True else cur
            paste_sprite(frame, spr_rgb, spr_a, spr_tip, tips[f])
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        err = proc.stderr.read().decode(errors="replace")
        if proc.wait() != 0:
            die("ffmpeg falhou na cena %d:\n%s" % (idx, "\n".join(err.strip().splitlines()[-10:])))
    except BrokenPipeError:
        die("ffmpeg encerrou antes do fim:\n" + proc.stderr.read().decode(errors="replace")[-600:])
    part.rename(final)
    return final, down, paper_end(cur)


def paper_end(cur):
    return None


# ----------------------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser(description="Video de rabisco preto e branco (lapis desenhando) de ate 60 s.")
    ap.add_argument("project", help="caminho do project.json")
    ap.add_argument("--out", help="MP4 de saida (padrao: <pasta do projeto>/video_final.mp4)")
    ap.add_argument("--brand", help="brand.json alternativo")
    ap.add_argument("--fit", action="store_true", help="encurta as cenas (sem voz) para caber no limite")
    ap.add_argument("--check-only", action="store_true", help="so mostra o plano de tempos")
    ap.add_argument("--preview", action="store_true", help="render rapido em 540x960")
    args = ap.parse_args()
    need("ffmpeg")
    need("ffprobe")

    proj_path = Path(args.project).resolve()
    base = proj_path.parent
    proj = json.loads(proj_path.read_text(encoding="utf-8"))
    brand = json.loads((Path(args.brand) if args.brand else SKILL_DIR / "brand" / "brand.json").read_text(encoding="utf-8"))
    wm_cfg = {**brand["marca_dagua"], **(proj.get("marca_dagua") or {})}
    cap_cfg = proj.get("legenda") or {}
    cta_cfg = proj.get("cta") or {}
    audio_cfg = proj.get("audio") or {}
    tool = proj.get("ferramenta", "marcador")
    if tool not in ("marcador", "lapis", "lapis-solto"):
        die("ferramenta deve ser 'marcador', 'lapis' ou 'lapis-solto'.")
    ink_val = np.array([22, 22, 24], np.float32) if tool == "marcador" else np.array([52, 52, 56], np.float32)
    max_s = float(proj.get("max_segundos", 60))
    scenes = proj.get("cenas") or []
    if not scenes:
        die("project.json sem 'cenas'.")

    def res(p):
        p = Path(p)
        return p if p.is_absolute() else base / p

    for i, sc in enumerate(scenes, 1):
        if not (sc.get("imagem") or sc.get("escrever")):
            die(f"Cena {i} precisa de 'imagem' e/ou 'escrever'.")
        if sc.get("imagem") and not res(sc["imagem"]).exists():
            die(f"Imagem da cena {i} nao encontrada: {sc['imagem']}")

    voice = res(audio_cfg["voz"]) if audio_cfg.get("voz") else None
    if voice and not voice.exists():
        die(f"Voz nao encontrada: {voice}")
    music = res(audio_cfg["musica"]) if audio_cfg.get("musica") else None
    if music and not music.exists():
        die(f"Musica nao encontrada: {music}")
    cta_on = cta_cfg.get("ativo", True)
    cta_dur = float(cta_cfg.get("duracao", 4.5)) if cta_on else 0.0

    words = [count_words(sc.get("texto", "")) for sc in scenes]
    explicit = [sc.get("duracao") for sc in scenes]
    need_write = [1.6 + 0.11 * len(sc.get("escrever", "")) + (2.0 if sc.get("imagem") else 0) for sc in scenes]
    per_scene = all(sc.get("voz") for sc in scenes)
    scene_voices = [res(sc["voz"]) for sc in scenes] if per_scene else []
    for sc, v in zip(scenes, scene_voices):
        if v.exists():
            sc["_fala_dur"] = probe_duration(v)
    for v in scene_voices:
        if not v.exists():
            die(f"Voz da cena nao encontrada: {v}")
    if per_scene:
        voice = None
        tail = float(audio_cfg.get("voz_tail", 0.7))
        durs = []
        for i, (sc, v) in enumerate(zip(scenes, scene_voices)):
            d = probe_duration(v) + tail + (0.5 if i == len(scenes) - 1 else 0)
            floor = 5.0 if sc.get("imagem") else 2.4 + 0.08 * len(sc.get("escrever", ""))
            if sc.get("imagem") and sc.get("escrever"):
                floor += 1.5
            durs.append(max(d, floor, float(sc.get("duracao_min", 0))))
    elif voice:
        vdur = probe_duration(voice) + float(audio_cfg.get("voz_tail", 0.4))
        if all(explicit):
            durs = [float(x) for x in explicit]
        else:
            tw = sum(max(w, 1) for w in words)
            durs = [vdur * max(w, 1) / tw for w in words]
    elif not per_scene:
        durs = [float(e) if e else max(MIN_SCENE, w / WORDS_PER_SECOND + 0.8, nw) for e, w, nw in zip(explicit, words, need_write)]

    total = sum(durs) + cta_dur
    if total > max_s:
        if args.fit and not voice:
            factor = (max_s - 1.0 - cta_dur) / sum(durs)
            if factor < 0.65:
                die("Roteiro longo demais para 60 s mesmo comprimindo. Corte cenas/texto.", 2)
            durs = [max(d * factor, 2.6) for d in durs]
            print(f"AVISO: cenas comprimidas em {factor:.0%} para caber em {max_s:.0f} s.")
        else:
            die(f"Duracao prevista {total:.1f} s passa do limite de {max_s:.0f} s (excesso {total - max_s:.1f} s). "
                "Corte cenas/texto ou use --fit (sem voz). Com voz, grave narracao mais curta.", 2)
    frames = [max(int(round(d * FPS)), 60) for d in durs]
    durs = [f / FPS for f in frames]
    total = sum(durs) + cta_dur
    print(f"Plano: {len(scenes)} cenas | {sum(durs):.1f} s + {cta_dur:.1f} s de tela final = {total:.1f} s (limite {max_s:.0f} s)")
    for i, (sc, d) in enumerate(zip(scenes, durs), 1):
        print(f"  cena {i:02d}: {d:5.1f} s  {(sc.get('escrever') or sc.get('texto') or sc.get('imagem', ''))[:56]}")
    if total > max_s + 0.05:
        die("Plano ainda acima do limite.", 2)
    if args.check_only:
        return

    s = 0.5 if args.preview else 1.0
    W, H = int(BASE_W * s), int(BASE_H * s)
    out = Path(args.out) if args.out else base / ("video_preview.mp4" if args.preview else "video_final.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    paper = make_paper(W, H)
    wm_file = SKILL_DIR / "brand" / wm_cfg["variantes"][wm_cfg.get("cor", "preto")]
    wm_w = int(wm_cfg["largura_pct"] / 100 * W)
    mx, my = int(wm_cfg["margem_direita_px"] * s), int(wm_cfg["margem_inferior_px"] * s)
    wm_op = wm_cfg.get("opacidade", 0.9)
    sfx_on = audio_cfg.get("som_lapis", True)

    tmp = Path(tempfile.mkdtemp(prefix="vrl_"))
    try:
        shutil.copytree(FONT_DIR, tmp / "fonts")
        files, sfx = [], []
        for i, (sc, d) in enumerate(zip(scenes, durs), 1):
            fpath, down, _ = render_scene(sc, i, d, W, H, s, paper, tool, ink_val, tmp, tmp / "fonts", wm_file, wm_w, mx, my,
                                          wm_op, cap_cfg, args.preview, res, seed=11 + i)
            files.append(fpath)
            if sfx_on:
                sfx.append(pen_sound(down, int(d * SR), seed=i))
        if cta_on:
            cta_png = tmp / "cta.png"
            render_cta(cta_png, brand, cta_cfg, W, H, s)
            n = int(round(cta_dur * FPS))
            part, fin = tmp / "scene_cta.part.mp4", tmp / "scene_cta.mp4"
            paper_c = PAPER_HEX.replace("#", "0x")
            run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", "cta.png", "-vf",
                 f"zoompan=z='1+0.04*on/{max(n - 1, 1)}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d={n}:s={W}x{H}:fps={FPS},"
                 f"format=yuv420p,fade=t=in:st=0:d=0.3:color={paper_c},fade=t=out:st={cta_dur - 0.3:.3f}:d=0.3:color={paper_c}",
                 "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "28" if args.preview else "18",
                 "-pix_fmt", "yuv420p", "-r", str(FPS), part.name], cwd=tmp)
            part.rename(fin)
            files.append(fin)
            if sfx_on:
                sfx.append(np.zeros(int(cta_dur * SR), np.float32))

        (tmp / "list.txt").write_text("".join(f"file '{p.name}'\n" for p in files), encoding="utf-8")
        silent = tmp / "video_mudo.mp4"
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy",
             silent.name], cwd=tmp)
        vid_dur = probe_duration(silent)

        if per_scene:
            parts = []
            for i, (v, d) in enumerate(zip(scene_voices, durs), 1):
                o = tmp / f"vs_{i:02d}.wav"
                run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(v), "-af", f"aresample=44100,apad=whole_dur={d:.3f}",
                     "-t", f"{d:.3f}", "-ac", "1", o.name], cwd=tmp)
                parts.append(o.name)
            if cta_on:
                run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t",
                     f"{cta_dur:.3f}", "vs_cta.wav"], cwd=tmp)
                parts.append("vs_cta.wav")
            (tmp / "vlist.txt").write_text("".join(f"file '{n}'\n" for n in parts), encoding="utf-8")
            run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "vlist.txt", "-c", "copy",
                 "voz_all.wav"], cwd=tmp)
            voice = tmp / "voz_all.wav"
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(silent)]
        filt, labels, idx = [], [], 1
        if voice:
            cmd += ["-i", str(voice)]
            filt.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo,volume={audio_cfg.get('voz_volume', 1.0)}[va]")
            labels.append("[va]"); idx += 1
        if music:
            cmd += ["-stream_loop", "-1", "-i", str(music)]
            vol = audio_cfg.get("musica_volume", 0.14 if voice else 0.6)
            filt.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo,volume={vol},afade=t=in:d=1,"
                        f"afade=t=out:st={max(vid_dur - 2, 0):.2f}:d=2[ma]")
            labels.append("[ma]"); idx += 1
        if sfx_on and sfx:
            wav = tmp / "sfx.wav"
            data = np.concatenate(sfx)
            with wave.open(str(wav), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
                w.writeframes((np.clip(data, -1, 1) * 32767).astype(np.int16).tobytes())
            cmd += ["-i", str(wav)]
            filt.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo,volume={audio_cfg.get('som_lapis_volume', 0.5)}[sa]")
            labels.append("[sa]"); idx += 1
        if labels:
            mix = "".join(labels)
            filt.append(f"{mix}amix=inputs={len(labels)}:duration=longest:normalize=0,atrim=0:{vid_dur:.3f}[a]" if len(labels) > 1
                        else f"{labels[0]}atrim=0:{vid_dur:.3f}[a]")
            cmd += ["-filter_complex", ";".join(filt), "-map", "0:v", "-map", "[a]"]
        else:
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-map", "0:v", "-map", f"{idx}:a"]
        cmd += ["-t", f"{vid_dur:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
        run(cmd)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    final_dur = probe_duration(out)
    if final_dur > max_s + 0.05:
        out.unlink(missing_ok=True)
        die(f"Video final com {final_dur:.1f} s passou de {max_s:.0f} s. Arquivo removido.", 3)
    if proj.get("post"):
        cap_out = out.parent / "legenda.txt"
        write_post_caption(cap_out, proj["post"], brand)
        print(f"Legenda do post: {cap_out}")
    print(f"PRONTO: {out}  ({final_dur:.1f} s, {out.stat().st_size / 1e6:.1f} MB, {W}x{H}, {FPS} fps)")


if __name__ == "__main__":
    main()
