#!/usr/bin/env python3
"""
narrar_kokoro.py - gera a NARRACAO de cada cena (voz em portugues do Brasil) com o Kokoro, offline e GRATIS,
e grava o campo "voz" em cada cena do project.json. O motor ajusta o tempo de cada cena a fala.

Uso:
  pip install kokoro-onnx soundfile
  python3 narrar_kokoro.py project.json                 # voz masculina (pm_alex)
  python3 narrar_kokoro.py project.json --voz pf_dora   # feminina; outras: pm_santa
  python3 narrar_kokoro.py project.json --velocidade 0.92

Texto falado de cada cena: campo "fala" (se existir) ou "texto". Modelos (~350 MB) baixados uma vez de
github.com/thewh1teagle/kokoro-onnx (releases) para ~/.cache/skills-video/. Sem custo e sem API paga.
"""
import argparse, json, sys, urllib.request
from pathlib import Path

BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = ["kokoro-v1.0.onnx", "voices-v1.0.bin"]

def get_models():
    d = Path.home() / ".cache" / "skills-video"; d.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        if not (d / f).exists() or (d / f).stat().st_size < 1_000_000:
            print(f"Baixando {f} (so na primeira vez)...")
            urllib.request.urlretrieve(BASE + f, d / f)
    return d / FILES[0], d / FILES[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("--voz", default="pm_alex")
    ap.add_argument("--velocidade", type=float, default=0.93)
    a = ap.parse_args()
    try:
        import soundfile as sf
        from kokoro_onnx import Kokoro
    except ImportError:
        sys.exit("Instale:  pip install kokoro-onnx soundfile")
    pp = Path(a.project).resolve(); proj = json.loads(pp.read_text(encoding="utf-8"))
    model, voices = get_models()
    k = Kokoro(str(model), str(voices))
    out = pp.parent / "voz"; out.mkdir(exist_ok=True)
    for i, sc in enumerate(proj["cenas"], 1):
        txt = (sc.get("fala") or sc.get("texto") or "").strip()
        if not txt:
            sc.pop("voz", None); continue
        samples, sr = k.create(txt, voice=a.voz, speed=a.velocidade, lang="pt-br")
        f = out / f"cena_{i:02d}.wav"; sf.write(f, samples, sr)
        sc["voz"] = f"voz/{f.name}"; print(f"cena {i:02d}: {len(samples)/sr:.1f}s")
    pp.write_text(json.dumps(proj, ensure_ascii=False, indent=2), encoding="utf-8")
    print("project.json atualizado com 'voz' por cena.")

if __name__ == "__main__":
    main()
