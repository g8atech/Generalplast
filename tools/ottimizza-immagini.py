#!/usr/bin/env python3
"""
Genera le immagini pubblicate a partire dagli originali in sorgenti/.

Gli originali restano intatti e fuori dalla cartella pubblicata: in public/
finiscono solo le versioni ridimensionate alla misura in cui vengono
realmente mostrate e convertite in WebP.

  python3 tools/ottimizza-immagini.py            # rigenera quelle mancanti
  python3 tools/ottimizza-immagini.py --tutte    # rigenera tutto

La larghezza di destinazione è il doppio di quella di visualizzazione, così
anche sugli schermi ad alta densità non si vede differenza. Servire un file
da 2048 px in un riquadro da 560 è peso scaricato e mai usato.
"""
import argparse
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Serve Pillow:  pip install --break-system-packages pillow")

RADICE = Path(__file__).resolve().parent.parent
SORGENTI = RADICE / "sorgenti"
PUBBLICO = RADICE / "public"

# nome originale -> (lato lungo massimo, qualità, nota sul perché)
IMMAGINI = {
    "hero.png":          (1920, 82, "sfondo a tutta pagina della home"),
    "pressa-grande.jpg": (1920, 80, "sfondo a tutta pagina conto terzi"),
    "azienda.jpg":       (1400, 80, "riquadro ~560 px nella home"),
    "catalogo.jpg":      (1400, 86, "texture molto fine: regge male una qualità bassa"),
    "consulenza.jpg":    (1200, 80, "riquadro ~560 px, alto 288-384"),
    "servizi.jpg":       (1200, 80, "riquadro ~560 px, alto 288-384"),
    "stampi.jpg":        (1200, 80, "riquadro ~560 px, alto 288-384"),
    "logo.png":          (900,  92, "alto 44-48 px; sorgente ampia per un ricampionamento fedele"),
}

# Le gif animate diventano WebP animato: stesso numero di fotogrammi e
# stessa velocità, solo un formato che non sprechi.
ANIMATE = {
    "collaudo.gif":   70,
    "stampaggio.gif": 70,
    "estrusione.gif": 70,
}


def kb(p):
    return p.stat().st_size / 1024


def statica(nome, lato, qualita):
    src = SORGENTI / nome
    dst = PUBBLICO / (Path(nome).stem + ".webp")
    im = Image.open(src)
    originale = im.size
    if max(im.size) > lato:
        im.thumbnail((lato, lato), Image.LANCZOS)
    alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
    im = im.convert("RGBA" if alpha else "RGB")
    im.save(dst, "WEBP", quality=qualita, method=6)
    return dst, originale, im.size, kb(src), kb(dst)


def animata(nome, qualita):
    src = SORGENTI / nome
    dst = PUBBLICO / (Path(nome).stem + ".webp")
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(src),
         "-c:v", "libwebp_anim", "-lossless", "0", "-q:v", str(qualita),
         "-loop", "0", "-preset", "photo", str(dst)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg su {nome}: {r.stderr.strip()[:200]}")
    return dst, kb(src), kb(dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tutte", action="store_true", help="rigenera anche ciò che esiste già")
    a = ap.parse_args()

    if not SORGENTI.is_dir():
        sys.exit(f"Manca la cartella {SORGENTI}: mettici gli originali.")

    prima = dopo = 0.0
    print(f"{'file':22s} {'originale':>16s} {'pubblicato':>16s}  {'peso':>18s}")
    print("-" * 78)

    for nome, (lato, q, _) in IMMAGINI.items():
        if not (SORGENTI / nome).exists():
            print(f"{nome:22s}  manca in sorgenti/, saltato")
            continue
        dst = PUBBLICO / (Path(nome).stem + ".webp")
        if dst.exists() and not a.tutte:
            print(f"{nome:22s}  già presente, saltato")
            continue
        _, o, n, ko, kn = statica(nome, lato, q)
        prima += ko; dopo += kn
        print(f"{nome:22s} {o[0]:>7}×{o[1]:<8} {n[0]:>7}×{n[1]:<8}  {ko:>7.0f} → {kn:>6.0f} KB")

    for nome, q in ANIMATE.items():
        if not (SORGENTI / nome).exists():
            print(f"{nome:22s}  manca in sorgenti/, saltato")
            continue
        dst = PUBBLICO / (Path(nome).stem + ".webp")
        if dst.exists() and not a.tutte:
            print(f"{nome:22s}  già presente, saltato")
            continue
        _, ko, kn = animata(nome, q)
        prima += ko; dopo += kn
        print(f"{nome:22s} {'animata':>16s} {'webp animato':>16s}  {ko:>7.0f} → {kn:>6.0f} KB")

    if prima:
        print("-" * 78)
        print(f"{'TOTALE':22s} {'':33s}  {prima:>7.0f} → {dopo:>6.0f} KB "
              f"({100 * (1 - dopo / prima):.0f}% in meno)")


if __name__ == "__main__":
    main()
