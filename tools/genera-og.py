#!/usr/bin/env python3
"""
Genera l'immagine di anteprima per le condivisioni (Open Graph), 1200×630.

È quella che compare quando il sito viene incollato in WhatsApp, LinkedIn o
in una mail. Senza, il link appare nudo e sembra poco curato.

  python3 tools/genera-og.py --sfondo sorgenti/hero.png --logo public/logo.webp \
      --testo "Stampaggio e lavorazione materie plastiche dal 1968"
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Serve Pillow:  pip install --break-system-packages pillow")

LARG, ALT = 1200, 630


def carattere(dim, grassetto=True):
    candidati = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if grassetto
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for c in candidati:
        if Path(c).exists():
            return ImageFont.truetype(c, dim)
    return ImageFont.load_default()


def a_capo(testo, font, disegno, larghezza):
    parole, righe, riga = testo.split(), [], ""
    for p in parole:
        prova = (riga + " " + p).strip()
        if disegno.textlength(prova, font=font) <= larghezza:
            riga = prova
        else:
            if riga:
                righe.append(riga)
            riga = p
    if riga:
        righe.append(riga)
    return righe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sfondo", required=True)
    ap.add_argument("--logo")
    ap.add_argument("--testo", default="")
    ap.add_argument("--uscita", default="public/og.jpg")
    ap.add_argument("--colore", default="#c72026")
    a = ap.parse_args()

    rgb = tuple(int(a.colore.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))

    # fondo ritagliato al formato richiesto, senza deformare
    sf = Image.open(a.sfondo).convert("RGB")
    k = max(LARG / sf.width, ALT / sf.height)
    sf = sf.resize((round(sf.width * k), round(sf.height * k)), Image.LANCZOS)
    sx, sy = (sf.width - LARG) // 2, (sf.height - ALT) // 2
    tela = sf.crop((sx, sy, sx + LARG, sy + ALT))

    # velatura scura: il testo bianco deve restare leggibile su qualsiasi foto
    velo = Image.new("RGBA", (LARG, ALT), (0, 0, 0, 0))
    d = ImageDraw.Draw(velo)
    for y in range(ALT):
        d.line([(0, y), (LARG, y)], fill=(14, 16, 20, int(120 + 115 * (y / ALT))))
    tela = Image.alpha_composite(tela.convert("RGBA"), velo)

    d = ImageDraw.Draw(tela)
    d.rectangle([0, ALT - 12, LARG, ALT], fill=(*rgb, 255))

    bordo = 72
    y = ALT - 150

    if a.testo:
        f = carattere(50)
        righe = a_capo(a.testo, f, d, LARG - bordo * 2)
        y = ALT - 120 - len(righe) * 62
        for r in righe:
            d.text((bordo, y), r, font=f, fill=(255, 255, 255))
            y += 62

    if a.logo:
        lg = Image.open(a.logo).convert("RGBA")
        lg.thumbnail((360, 110), Image.LANCZOS)
        # il logo è rosso su trasparente: su foto scura va portato a bianco
        px = lg.load()
        for yy in range(lg.size[1]):
            for xx in range(lg.size[0]):
                r, g, b, al = px[xx, yy]
                if al > 0:
                    px[xx, yy] = (255, 255, 255, al)
        tela.alpha_composite(lg, (bordo, 68))

    Path(a.uscita).parent.mkdir(parents=True, exist_ok=True)
    finale = tela.convert("RGB")
    # è una fotografia: in JPEG pesa un quinto, a parità di resa
    if a.uscita.lower().endswith((".jpg", ".jpeg")):
        finale.save(a.uscita, "JPEG", quality=86, optimize=True, progressive=True)
    else:
        finale.save(a.uscita, "PNG", optimize=True)
    kb = Path(a.uscita).stat().st_size / 1024
    print(f"{a.uscita}: {LARG}×{ALT}, {kb:.0f} KB")


if __name__ == "__main__":
    main()
