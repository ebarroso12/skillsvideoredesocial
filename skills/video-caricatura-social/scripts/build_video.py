#!/usr/bin/env python3
"""
build_video.py - monta um video vertical (9:16) para redes sociais, com no maximo 60 s.

Entrada : um project.json (ver templates/project.example.json) com as cenas (imagens ja
          prontas: caricatura/desenho), o texto de cada cena, audio opcional e a marca.
Saida   : MP4 1080x1920 30 fps (H.264 + AAC) e, se pedido, legenda.txt para o post.

O que o script faz:
  * ajusta cada imagem para 9:16 (corte centralizado ou fundo desfocado)
  * movimento suave (zoom / pan) em cada cena
  * legenda dourada palavra por palavra, em fonte serifada
  * marca d'agua no canto inferior direito (cor escolhida pelo contraste com o fundo)
  * tela final com chamada para consulta (dados vindos de brand/brand.json)
  * voz e musica opcionais
  * TRAVA de duracao: nunca entrega mais que max_seconds (padrao 60)

Dependencias: python3, Pillow, ffmpeg/ffprobe (com libass).
Uso:
  python3 build_video.py project.json                 # render final
  python3 build_video.py project.json --check-only    # so mostra o plano de tempos
  python3 build_video.py project.json --preview       # render rapido em baixa resolucao
  python3 build_video.py project.json --fit           # encurta cenas (sem voz) para caber
"""
import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat
except ImportError:  # pragma: no cover
    sys.exit("Falta o Pillow. Instale com:  pip install pillow")

SKILL_DIR = Path(__file__).resolve().parent.parent
FONT_DIR = SKILL_DIR / "fonts"
BASE_W, BASE_H = 1080, 1920
FPS = 30
WORDS_PER_SECOND = 2.6      # ritmo de leitura/fala em PT-BR para estimar tempos
MIN_SCENE = 2.5
SCENE_PAD = 0.5
FADE = 0.25
MOTIONS = ["zoom_in", "pan_right", "zoom_out", "pan_left", "pan_up", "zoom_in", "pan_down"]


# ----------------------------------------------------------------------------- utils
def die(msg, code=1):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(code)


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        tail = "\n".join(r.stderr.strip().splitlines()[-12:])
        die(f"ffmpeg falhou ({' '.join(map(str, cmd[:3]))} ...):\n{tail}")
    return r


def need(binary):
    if not shutil.which(binary):
        die(f"'{binary}' nao encontrado. Instale o ffmpeg (https://ffmpeg.org/download.html).")


def probe_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        die(f"Nao consegui ler a duracao de {path}")


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hex_to_ass(h):
    r, g, b = hex_to_rgb(h)
    return f"&H00{b:02X}{g:02X}{r:02X}"


def lum(rgb):
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def count_words(text):
    return len(re.findall(r"\S+", text or ""))


def ass_time(t):
    t = max(t, 0)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


# ----------------------------------------------------------------------------- imagens
def prepare_image(src, dst, mode="auto", focus=(0.5, 0.5)):
    """Gera um PNG 2160x3840 (9:16) a partir da imagem de origem."""
    CW, CH = BASE_W * 2, BASE_H * 2
    im = Image.open(src).convert("RGB")
    w, h = im.size
    ratio = w / h
    target = CW / CH
    if mode == "auto":
        mode = "cover" if abs(ratio / target - 1) <= 0.12 else "blur"

    def cover(img):
        s = max(CW / img.width, CH / img.height)
        nw, nh = math.ceil(img.width * s), math.ceil(img.height * s)
        img = img.resize((nw, nh), Image.LANCZOS)
        fx, fy = focus
        left = int(min(max(fx * nw - CW / 2, 0), nw - CW))
        top = int(min(max(fy * nh - CH / 2, 0), nh - CH))
        return img.crop((left, top, left + CW, top + CH))

    if mode == "cover":
        out = cover(im)
    else:  # blur: fundo desfocado + imagem inteira centralizada
        bg = cover(im).filter(ImageFilter.GaussianBlur(60))
        bg = Image.eval(bg, lambda v: int(v * 0.65))
        s = min(CW / im.width, CH / im.height)
        fg = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        bg.paste(fg, ((CW - fg.width) // 2, (CH - fg.height) // 2))
        out = bg
    out.save(dst, "PNG")
    return out


def corner_luminance(img, wm_cfg):
    """Luminancia media da regiao onde a marca d'agua vai ficar."""
    W, H = img.size
    k = W / BASE_W
    ww = wm_cfg["largura_pct"] / 100 * BASE_W
    x1 = BASE_W - wm_cfg["margem_direita_px"]
    x0 = x1 - ww
    y1 = BASE_H - wm_cfg["margem_inferior_px"]
    y0 = y1 - ww
    box = tuple(int(v * k) for v in (x0, y0, x1, y1))
    return lum(ImageStat.Stat(img.crop(box)).mean[:3])


def pick_watermark_variant(avg_lum):
    """Escolhe dourado/branco/azul pelo melhor contraste com o fundo."""
    cands = {"branco": 255.0, "azul": 22.0, "dourado": 175.0}
    contrast = {k: abs(avg_lum - v) for k, v in cands.items()}
    if contrast["dourado"] >= 85:  # prefere a cor da marca quando legivel
        return "dourado"
    return max(("branco", "azul"), key=lambda k: contrast[k])


# ----------------------------------------------------------------------------- legenda
WEAK_END = {"a", "o", "e", "as", "os", "um", "uma", "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
            "que", "com", "por", "para", "pra", "se", "me", "te", "lhe", "ao", "à", "ou", "mas", "não", "sua", "seu", "meu", "minha"}


def chunk_text(text, max_words=3):
    """Divide o texto em blocos curtos, quebrando em pontuacao e evitando terminar em artigo/preposicao."""
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


def build_ass(text, duration, cfg, colors, y_pos):
    chunks = chunk_text(text, cfg.get("palavras_por_bloco", 3))
    size = cfg.get("tamanho", 100)
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Cap,Playfair Display,{size},{hex_to_ass(colors['legenda_dourado'])},&H000000FF,"
        f"{hex_to_ass(colors['contorno_legenda'])},&H90000000,-1,0,0,0,100,100,1,0,1,7,3,5,90,90,0,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    if not chunks:
        return header
    start0, end_all = 0.15, max(duration - 0.2, 0.5)
    span = end_all - start0
    weights = [len(c) + 2 for c in chunks]
    total = sum(weights)
    t = start0
    lines = []
    for c, wgt in zip(chunks, weights):
        d = span * wgt / total
        text_ass = c.replace("{", "(").replace("}", ")")
        lines.append(
            f"Dialogue: 0,{ass_time(t)},{ass_time(t + d)},Cap,,0,0,0,,"
            f"{{\\an5\\pos(540,{y_pos})\\fad(120,60)\\fscx90\\fscy90\\t(0,140,\\fscx100\\fscy100)}}{text_ass}"
        )
        t += d
    return header + "\n".join(lines) + "\n"


# ----------------------------------------------------------------------------- movimento
def motion_exprs(name, n):
    n = max(n - 1, 1)
    c_x, c_y = "(iw-iw/zoom)/2", "(ih-ih/zoom)/2"
    if name == "zoom_in":
        return f"1+0.14*on/{n}", c_x, c_y
    if name == "zoom_out":
        return f"1.14-0.14*on/{n}", c_x, c_y
    if name == "pan_left":
        return "1.12", f"(iw-iw/zoom)*(1-on/{n})", c_y
    if name == "pan_right":
        return "1.12", f"(iw-iw/zoom)*on/{n}", c_y
    if name == "pan_up":
        return "1.12", c_x, f"(ih-ih/zoom)*(1-on/{n})"
    if name == "pan_down":
        return "1.12", c_x, f"(ih-ih/zoom)*on/{n}"
    return "1", c_x, c_y


# ----------------------------------------------------------------------------- tela final (CTA)
def _font(name, size):
    return ImageFont.truetype(str(FONT_DIR / name), size)


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_cta_card(dst, brand, cta_cfg, k=2):
    colors = brand["cores"]
    W, H = BASE_W * k, BASE_H * k
    top, bot = hex_to_rgb(colors["marinho"]), hex_to_rgb(colors["marinho_claro"])
    img = Image.new("RGB", (W, H))
    px = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        px.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    d = ImageDraw.Draw(img)
    gold = hex_to_rgb(colors["legenda_dourado"])
    bronze = hex_to_rgb(colors["bronze"])
    white = (245, 242, 236)
    cx = W // 2

    # logo
    logo_path = SKILL_DIR / "brand" / brand.get("cta_logo", "logos/logo-vertical-simbolo-dourado-texto-branco.png")
    y = 270 * k
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        lw = 620 * k
        lh = int(logo.height * lw / logo.width)
        logo = logo.resize((lw, lh), Image.LANCZOS)
        img.paste(logo, ((W - lw) // 2, y), logo)
        y += lh + 110 * k

    def centered(text, font, fill, y, max_w=900 * k, gap=10 * k):
        for line in _wrap(d, text, font, max_w):
            w = d.textlength(line, font=font)
            d.text((cx - w / 2, y), line, font=font, fill=fill)
            y += font.size + gap
        return y

    headline = cta_cfg.get("titulo", "Agende sua consulta")
    y = centered(headline, _font("PlayfairDisplay-Bold.ttf", 84 * k), gold, y)
    sub = cta_cfg.get("subtitulo", "e dê o primeiro passo para cuidar de você")
    y = centered(sub, _font("Montserrat-Regular.ttf", 42 * k), white, y + 14 * k)

    y += 60 * k
    d.line([(cx - 90 * k, y), (cx + 90 * k, y)], fill=bronze, width=3 * k)
    y += 70 * k

    f_lbl = _font("Montserrat-SemiBold.ttf", 46 * k)
    y = centered(f"WhatsApp  {brand['whatsapp']}", f_lbl, gold, y)
    y += 44 * k
    f_addr = _font("Montserrat-Regular.ttf", 38 * k)
    for line in brand.get("endereco", []):
        y = centered(line, f_addr, white, y, gap=8 * k)
    y += 50 * k
    y = centered(brand["site"], _font("Montserrat-SemiBold.ttf", 42 * k), gold, y)
    if brand.get("instagram"):
        y = centered(brand["instagram"], _font("Montserrat-Regular.ttf", 38 * k), white, y + 4 * k)
    if brand.get("registro_profissional"):
        small = _font("Montserrat-Regular.ttf", 28 * k)
        txt = f"{brand['nome']} · {brand['registro_profissional']}"
        w = d.textlength(txt, font=small)
        d.text((cx - w / 2, H - 150 * k), txt, font=small, fill=(190, 186, 178))
    img.save(dst, "PNG")


# ----------------------------------------------------------------------------- legenda do post
def write_post_caption(dst, post, brand):
    corpo = (post.get("corpo") or "").strip()
    hashtags = post.get("hashtags") or brand.get("hashtags_base", [])
    partes = [corpo] if corpo else []
    if post.get("incluir_cta", True):
        bloco = [brand.get("cta_frase", "Agende sua consulta."), "", f"WhatsApp: {brand['whatsapp']}", ""]
        bloco += brand.get("endereco", [])
        bloco += ["", brand["site"]]
        reg = " — ".join(x for x in [brand.get("nome"), brand.get("registro_profissional")] if x)
        if reg:
            bloco.append(reg)
        partes.append("\n".join(bloco))
    if hashtags:
        partes.append(" ".join(hashtags))
    Path(dst).write_text("\n\n".join(partes) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser(description="Monta video vertical de ate 60 s para redes sociais.")
    ap.add_argument("project", help="caminho do project.json")
    ap.add_argument("--out", help="arquivo MP4 de saida (padrao: <pasta do projeto>/video_final.mp4)")
    ap.add_argument("--brand", help="brand.json alternativo")
    ap.add_argument("--fit", action="store_true", help="encurta as cenas (sem voz) para caber no limite")
    ap.add_argument("--check-only", action="store_true", help="so mostra o plano de tempos, sem renderizar")
    ap.add_argument("--preview", action="store_true", help="render rapido em 540x960")
    args = ap.parse_args()

    need("ffmpeg")
    need("ffprobe")

    proj_path = Path(args.project).resolve()
    base = proj_path.parent
    proj = json.loads(proj_path.read_text(encoding="utf-8"))
    brand_path = Path(args.brand) if args.brand else SKILL_DIR / "brand" / "brand.json"
    brand = json.loads(brand_path.read_text(encoding="utf-8"))
    wm_cfg = {**brand["marca_dagua"], **(proj.get("marca_dagua") or {})}
    cap_cfg = proj.get("legenda") or {}
    cta_cfg = proj.get("cta") or {}
    audio_cfg = proj.get("audio") or {}
    max_s = float(proj.get("max_segundos", 60))
    scenes = proj.get("cenas") or []
    if not scenes:
        die("project.json sem 'cenas'.")

    def res(p):
        p = Path(p)
        return p if p.is_absolute() else (base / p)

    for i, sc in enumerate(scenes, 1):
        if not res(sc["imagem"]).exists():
            die(f"Imagem da cena {i} nao encontrada: {sc['imagem']}")

    # ---- plano de tempos
    voice = res(audio_cfg["voz"]) if audio_cfg.get("voz") else None
    if voice and not voice.exists():
        die(f"Arquivo de voz nao encontrado: {voice}")
    music = res(audio_cfg["musica"]) if audio_cfg.get("musica") else None
    if music and not music.exists():
        die(f"Arquivo de musica nao encontrado: {music}")

    cta_on = cta_cfg.get("ativo", True)
    cta_dur = float(cta_cfg.get("duracao", 4.5)) if cta_on else 0.0

    words = [count_words(sc.get("texto", "")) for sc in scenes]
    explicit = [sc.get("duracao") for sc in scenes]
    if voice:
        vdur = probe_duration(voice) + float(audio_cfg.get("voz_tail", 0.4))
        if all(explicit):
            durs = [float(x) for x in explicit]
        else:
            tw = sum(max(w, 1) for w in words)
            durs = [vdur * max(w, 1) / tw for w in words]
    else:
        durs = [float(e) if e else max(MIN_SCENE, w / WORDS_PER_SECOND + SCENE_PAD) for e, w in zip(explicit, words)]

    total = sum(durs) + cta_dur
    if total > max_s:
        over = total - max_s
        if args.fit and not voice:
            target = max_s - 1.0 - cta_dur
            factor = target / sum(durs)
            if factor < 0.6:
                die("Roteiro longo demais para caber em 60 s mesmo comprimindo. Corte texto/cenas.", 2)
            durs = [max(d * factor, 1.8) for d in durs]
            total = sum(durs) + cta_dur
            print(f"AVISO: cenas comprimidas em {factor:.0%} para caber em {max_s:.0f} s.")
        else:
            die(
                f"Duracao prevista {total:.1f} s passa do limite de {max_s:.0f} s (excesso {over:.1f} s). "
                "Corte texto/cenas, ou use --fit (sem voz). Com voz, grave uma narracao mais curta.",
                2,
            )
    frames = [max(int(round(d * FPS)), int(FADE * 2 * FPS) + 2) for d in durs]
    durs = [f / FPS for f in frames]
    total = sum(durs) + cta_dur

    print(f"Plano: {len(scenes)} cenas | {sum(durs):.1f} s de cenas + {cta_dur:.1f} s de tela final = {total:.1f} s (limite {max_s:.0f} s)")
    for i, (sc, d) in enumerate(zip(scenes, durs), 1):
        print(f"  cena {i:02d}: {d:5.1f} s  {sc.get('texto', '')[:60]}")
    if args.check_only:
        return

    scale = 0.5 if args.preview else 1.0
    W, H = int(BASE_W * scale), int(BASE_H * scale)
    out = Path(args.out) if args.out else base / ("video_preview.mp4" if args.preview else "video_final.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.mkdtemp(prefix="vcs_"))
    try:
        shutil.copytree(FONT_DIR, tmp / "fonts")

        # ---- imagens 9:16 + marca d'agua
        prepared, lums = [], []
        for i, sc in enumerate(scenes, 1):
            dst = tmp / f"img_{i:02d}.png"
            focus = tuple(sc.get("foco", (0.5, 0.5)))
            im = prepare_image(res(sc["imagem"]), dst, sc.get("ajuste", "auto"), focus)
            prepared.append(dst)
            lums.append(corner_luminance(im, wm_cfg))
        variant = wm_cfg.get("cor", "auto")
        if variant == "auto":
            variant = pick_watermark_variant(sum(lums) / len(lums))
        wm_file = SKILL_DIR / "brand" / wm_cfg["variantes"][variant]
        wm_w = int(wm_cfg["largura_pct"] / 100 * W)
        mx = int(wm_cfg["margem_direita_px"] * scale)
        my = int(wm_cfg["margem_inferior_px"] * scale)
        print(f"Marca d'agua: simbolo {variant}")

        # ---- renderiza cada cena (1 encode por cena, com legenda + marca d'agua)
        scene_files = []
        y_pos = int(cap_cfg.get("posicao_y", 1280))
        for i, (sc, d, n, img) in enumerate(zip(scenes, durs, frames, prepared), 1):
            ass_name = f"cap_{i:02d}.ass"
            (tmp / ass_name).write_text(
                build_ass(sc.get("texto", ""), d, cap_cfg, brand["cores"], y_pos), encoding="utf-8")
            mot = sc.get("movimento") or MOTIONS[(i - 1) % len(MOTIONS)]
            z, x, y = motion_exprs(mot, n)
            fade_in = FADE if i > 1 else 0.15
            fg = (
                f"[0:v]zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS}[bg];"
                f"[1:v]scale={wm_w}:-1,format=rgba,colorchannelmixer=aa={wm_cfg['opacidade']}[wm];"
                f"[bg][wm]overlay=x=W-w-{mx}:y=H-h-{my}:shortest=1,format=yuv420p,"
                f"ass={ass_name}:fontsdir=fonts,"
                f"fade=t=in:st=0:d={fade_in},fade=t=out:st={d - FADE:.3f}:d={FADE}[v]"
            )
            tmp_out = tmp / f"scene_{i:02d}.part.mp4"
            final = tmp / f"scene_{i:02d}.mp4"
            run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                 "-i", img.name, "-loop", "1", "-i", str(wm_file),
                 "-filter_complex", fg, "-map", "[v]", "-frames:v", str(n), "-an",
                 "-c:v", "libx264", "-preset", "ultrafast" if args.preview else "veryfast",
                 "-crf", "28" if args.preview else "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
                 str(tmp_out.name)], cwd=tmp)
            tmp_out.rename(final)
            scene_files.append(final)
            print(f"  cena {i:02d}/{len(scenes)} ok")

        # ---- tela final (CTA)
        if cta_on:
            cta_png = tmp / "cta.png"
            render_cta_card(cta_png, brand, cta_cfg)
            n = int(round(cta_dur * FPS))
            z, x, y = motion_exprs("zoom_in", n)
            tmp_out = tmp / "scene_cta.part.mp4"
            final = tmp / "scene_cta.mp4"
            run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", "cta.png",
                 "-vf", f"zoompan=z='1+0.05*on/{max(n - 1, 1)}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},"
                        f"format=yuv420p,fade=t=in:st=0:d=0.35,fade=t=out:st={cta_dur - 0.3:.3f}:d=0.3",
                 "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast",
                 "-crf", "28" if args.preview else "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
                 str(tmp_out.name)], cwd=tmp)
            tmp_out.rename(final)
            scene_files.append(final)
            print("  tela final ok")

        # ---- concat sem re-encode
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{p.name}'\n" for p in scene_files), encoding="utf-8")
        silent = tmp / "video_mudo.mp4"
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", "list.txt", "-c", "copy", silent.name], cwd=tmp)
        vid_dur = probe_duration(silent)

        # ---- audio (voz + musica, ou trilha silenciosa)
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(silent)]
        filt, labels = [], []
        idx = 1
        if voice:
            cmd += ["-i", str(voice)]
            filt.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo,volume={audio_cfg.get('voz_volume', 1.0)}[va]")
            labels.append("[va]")
            idx += 1
        if music:
            cmd += ["-stream_loop", "-1", "-i", str(music)]
            vol = audio_cfg.get("musica_volume", 0.14 if voice else 0.6)
            filt.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo,volume={vol},"
                        f"afade=t=in:d=1,afade=t=out:st={max(vid_dur - 2, 0):.2f}:d=2[ma]")
            labels.append("[ma]")
            idx += 1
        if labels:
            mix = "".join(labels)
            filt.append(f"{mix}amix=inputs={len(labels)}:duration=longest:normalize=0,atrim=0:{vid_dur:.3f}[a]"
                        if len(labels) > 1 else f"{labels[0]}atrim=0:{vid_dur:.3f}[a]")
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
        die(f"Video final com {final_dur:.1f} s ultrapassou {max_s:.0f} s. Arquivo removido.", 3)

    if proj.get("post"):
        cap_out = out.parent / "legenda.txt"
        write_post_caption(cap_out, proj["post"], brand)
        print(f"Legenda do post: {cap_out}")

    mb = out.stat().st_size / 1e6
    print(f"PRONTO: {out}  ({final_dur:.1f} s, {mb:.1f} MB, {W}x{H}, {FPS} fps)")


if __name__ == "__main__":
    main()
