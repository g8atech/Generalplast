#!/usr/bin/env python3
"""
Genera il set di icone del sito a partire dal logo del cliente.

Il logo di un'azienda è quasi sempre orizzontale: ridotto a 16 pixel
diventa illeggibile. Questo strumento isola il solo marchio (la forma
principale, scartando scritte, ® e frammenti) e lo monta in bianco su un
quadrato del colore del marchio, che a dimensioni minime si legge molto
meglio di una forma sottile su fondo trasparente.

  python3 tools/genera-favicon.py public/logo.png --colore "#c72026"

Opzioni utili quando il ritaglio automatico non indovina:
  --ritaglio x1,y1,x2,y2   limita l'area del logo da cui prendere il marchio
  --margine 0.08           spazio attorno al marchio (0.04-0.16)
  --su-chiaro              marchio colorato su bianco, invece che bianco su colore
"""
import argparse
import sys
from collections import deque

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Serve Pillow:  pip install --break-system-packages pillow")

import numpy as np

MISURE_ICO = [16, 32, 48]


def colore_dominante(img):
    """Il colore più presente fra i pixel opachi e non quasi-bianchi."""
    a = np.array(img)
    vis = a[:, :, 3] > 120
    px = a[vis][:, :3].astype(int)
    px = px[px.sum(axis=1) < 700]  # scarta il quasi-bianco
    if not len(px):
        return (0, 0, 0)
    q = (px // 24) * 24
    chiavi, conteggi = np.unique(q, axis=0, return_counts=True)
    return tuple(int(v) for v in chiavi[conteggi.argmax()])


def forma_principale(img):
    """Tiene solo la componente connessa più grande: via scritte, ® e residui."""
    a = np.array(img)
    pieno = a[:, :, 3] > 40
    h, w = pieno.shape
    visto = np.zeros_like(pieno, bool)
    migliore, quanti = None, 0
    for sy in range(0, h, 6):
        for sx in range(0, w, 6):
            if pieno[sy, sx] and not visto[sy, sx]:
                coda = deque([(sy, sx)])
                visto[sy, sx] = True
                comp = []
                while coda:
                    y, x = coda.popleft()
                    comp.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and pieno[ny, nx] and not visto[ny, nx]:
                            visto[ny, nx] = True
                            coda.append((ny, nx))
                if len(comp) > quanti:
                    quanti, migliore = len(comp), comp
    if migliore is None:
        return img
    maschera = np.zeros_like(pieno, bool)
    for y, x in migliore:
        maschera[y, x] = True
    fuori = a.copy()
    fuori[~maschera, 3] = 0
    r = Image.fromarray(fuori)
    return r.crop(r.getbbox())


def tinta(img, rgb):
    a = np.array(img).copy()
    a[:, :, 0], a[:, :, 1], a[:, :, 2] = rgb
    return Image.fromarray(a)


def icona(marchio, size, fondo, margine, raggio=0.0, opaca=False):
    sfondo = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(sfondo)
    box = [0, 0, size - 1, size - 1]
    if raggio:
        d.rounded_rectangle(box, radius=int(size * raggio), fill=fondo)
    else:
        d.rectangle(box, fill=fondo)
    lato = max(1, int(size * (1 - 2 * margine)))
    m = marchio.copy()
    m.thumbnail((lato, lato), Image.LANCZOS)
    sfondo.alpha_composite(m, ((size - m.size[0]) // 2, (size - m.size[1]) // 2))
    if opaca:
        piatta = Image.new("RGB", (size, size), fondo[:3])
        piatta.paste(sfondo, (0, 0), sfondo)
        return piatta
    return sfondo


def scrivi_ico(immagini, percorso):
    """Scrive un .ico con ogni misura resa alla sua risoluzione.

    Il salvataggio ICO di Pillow parte da una sola immagine e rimpicciolisce:
    a 16 px il risultato è più molle di un disegno fatto direttamente a 16.
    Il contenitore ICO è semplice, e dal 2007 accetta PNG al suo interno.
    """
    import io, struct

    blocchi = []
    for im in immagini:
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        blocchi.append((im.size[0], buf.getvalue()))

    testa = struct.pack("<HHH", 0, 1, len(blocchi))
    offset = len(testa) + 16 * len(blocchi)
    voci, dati = b"", b""
    for lato, png in blocchi:
        voci += struct.pack(
            "<BBBBHHII", lato if lato < 256 else 0, lato if lato < 256 else 0,
            0, 0, 1, 32, len(png), offset,
        )
        dati += png
        offset += len(png)
    with open(percorso, "wb") as f:
        f.write(testa + voci + dati)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logo")
    ap.add_argument("--uscita", default="public")
    ap.add_argument("--colore", help='colore del quadrato, es. "#c72026"; se omesso si ricava dal logo')
    ap.add_argument("--margine", type=float, default=0.08)
    ap.add_argument("--ritaglio", help="x1,y1,x2,y2 — area del logo da cui prendere il marchio")
    ap.add_argument("--su-chiaro", action="store_true", help="marchio colorato su bianco")
    a = ap.parse_args()

    logo = Image.open(a.logo).convert("RGBA")
    if a.ritaglio:
        logo = logo.crop(tuple(int(v) for v in a.ritaglio.split(",")))

    marchio = forma_principale(logo)
    rgb = (
        tuple(int(a.colore.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        if a.colore
        else colore_dominante(marchio)
    )
    print(f"marchio isolato: {marchio.size[0]}×{marchio.size[1]} px")
    print(f"colore: #{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}")

    if a.su_chiaro:
        fondo, segno = (255, 255, 255, 255), tinta(marchio, rgb)
    else:
        fondo, segno = (*rgb, 255), tinta(marchio, (255, 255, 255))

    u = a.uscita.rstrip("/")
    scrivi_ico(
        [icona(segno, s, fondo, a.margine) for s in MISURE_ICO],
        f"{u}/favicon.ico",
    )
    icona(segno, 192, fondo, a.margine).save(f"{u}/icon-192.png")
    icona(segno, 512, fondo, a.margine).save(f"{u}/icon-512.png")
    # Apple arrotonda da sé e non gradisce la trasparenza: quadrato pieno,
    # con un filo di margine in più perché l'angolo non tagli il marchio.
    icona(segno, 180, fondo, a.margine + 0.04, opaca=True).save(f"{u}/apple-touch-icon.png")

    print(f"scritti in {u}/: favicon.ico ({'+'.join(map(str, MISURE_ICO))}), "
          f"icon-192.png, icon-512.png, apple-touch-icon.png")


if __name__ == "__main__":
    main()
