#!/usr/bin/env python3
"""gerar_trilha.py - trilha ambiente suave e emotiva (acordes de pad), gerada por codigo: sem direitos autorais, gratis.
Uso: python3 gerar_trilha.py trilha.wav [--segundos 60] [--clima triste|esperanca]"""
import argparse, wave
import numpy as np
SR = 44100
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("saida"); ap.add_argument("--segundos", type=float, default=60)
    ap.add_argument("--clima", default="triste"); a = ap.parse_args()
    n = int(a.segundos * SR); t = np.arange(n) / SR
    prog = {"triste": [("A", [220.0, 261.63, 329.63]), ("F", [174.61, 220.0, 261.63]), ("C", [196.0, 261.63, 329.63]), ("G", [196.0, 246.94, 293.66])],
            "esperanca": [("C", [261.63, 329.63, 392.0]), ("G", [196.0, 246.94, 392.0]), ("Am", [220.0, 261.63, 329.63]), ("F", [174.61, 261.63, 349.23])]}[a.clima]
    seg = 7.0; out = np.zeros(n)
    for ci in range(int(np.ceil(a.segundos / seg))):
        s0 = int(ci * seg * SR); s1 = min(int((ci + 1) * seg * SR + 2 * SR), n)
        tt = t[s0:s1] - t[s0]; env = np.minimum(tt / 2.0, 1) * np.minimum((tt[-1] - tt) / 2.0, 1)
        for f in prog[ci % 4][1]:
            for h, amp in ((1, 1.0), (2, 0.35), (3, 0.12)):
                out[s0:s1] += env * amp * np.sin(2 * np.pi * f * h * tt + 0.3 * np.sin(2 * np.pi * 0.2 * tt))
        out[s0:s1] += env * 0.5 * np.sin(2 * np.pi * (prog[ci % 4][1][0] / 2) * tt)
    out *= 0.5 + 0.1 * np.sin(2 * np.pi * 0.08 * t)
    # reverb simples
    for d, g in ((0.23, 0.35), (0.41, 0.25), (0.67, 0.18)):
        k = int(d * SR); out[k:] += g * out[:-k]
    out = out / np.max(np.abs(out)) * 0.8
    with wave.open(a.saida, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
    print("ok", a.saida)
if __name__ == "__main__":
    main()
