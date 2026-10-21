#!/usr/bin/env python3
"""Confronta le schermate, escludendo le aree occupate da gif animate."""
import sys, os, json
from PIL import Image, ImageChops, ImageDraw

C = sys.argv[1]
boxes = json.load(open(os.path.join(C, "gif-boxes.json"), encoding="utf-8"))
keys = sorted(f[: -len(".live.png")] for f in os.listdir(C) if f.endswith(".live.png"))

worst = 0
print(f"{'pagina':32s} {'differenza':>11s}  esito")
for k in keys:
    a = Image.open(f"{C}/{k}.live.png").convert("RGB")
    b = Image.open(f"{C}/{k}.new.png").convert("RGB")
    note = ""
    if a.size != b.size:
        note = f"  ALTEZZA {a.size[1]} vs {b.size[1]}"
        W, H = min(a.size[0], b.size[0]), min(a.size[1], b.size[1])
        a, b = a.crop((0, 0, W, H)), b.crop((0, 0, W, H))

    d = ImageChops.difference(a, b).convert("L").point(lambda x: 255 if x > 12 else 0)
    masked = 0
    dr = ImageDraw.Draw(d)
    for box in boxes.get(k, []):
        x0, y0, x1, y1 = box
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(d.size[0], x1), min(d.size[1], y1)
        if x1 > x0 and y1 > y0:
            masked += (x1 - x0) * (y1 - y0)
            dr.rectangle([x0, y0, x1, y1], fill=0)

    tot = a.size[0] * a.size[1] - masked
    n = sum(d.histogram()[13:])
    pct = 100 * n / max(tot, 1)
    worst = max(worst, pct)
    v = "identico" if pct < 0.05 else ("quasi identico" if pct < 0.5 else "DA VEDERE")
    print(f"{k:32s} {pct:>10.3f}%  {v}{note}")
    d.save(f"{C}/{k}.diff.png")

print(f"\npeggiore: {worst:.3f}%")
