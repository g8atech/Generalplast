#!/usr/bin/env python3
"""
Converte l'HTML renderizzato del sito attuale in componenti e pagine Astro,
mantenendo il markup invariato. Non reinterpreta il design: lo trasporta.
"""
import re, os, json, sys, html as htmlmod

SRC = sys.argv[1]
OUT = sys.argv[2]

PAGES = [
    # file sorgente,      rotta,                      nome file astro
    ("home.html",         "/",                        "index.astro"),
    ("lavorazione.html",  "/lavorazione-produzione",  "lavorazione-produzione.astro"),
    ("stampaggio.html",   "/stampaggio-conto-terzi",  "stampaggio-conto-terzi.astro"),
    ("privacy.html",      "/privacy",                 "privacy.astro"),
]


def read(f):
    return open(os.path.join(SRC, f), encoding="utf-8", errors="replace").read()


def clean(s):
    """Toglie i marcatori di React, lasciando intatto il markup."""
    s = re.sub(r"<!--\$-->|<!--/\$-->|<!--\s*-->", "", s)
    s = re.sub(r'\s*data-status="active"', "", s)
    s = re.sub(r'\s*aria-current="page"', "", s)
    s = s.replace(' class="flex items-center active"', ' class="flex items-center"')
    s = re.sub(r'([^"]*?)\s+active"', r'\1"', s) if False else s
    return s


def grab(h, pat):
    m = re.search(pat, h, re.S)
    return m.group(0) if m else None


def head_meta(h):
    def meta(attr, val):
        m = re.search(r'<meta\s+%s="%s"\s+content="([^"]*)"' % (attr, re.escape(val)), h)
        if not m:
            m = re.search(r'<meta\s+content="([^"]*)"\s+%s="%s"' % (attr, re.escape(val)), h)
        return htmlmod.unescape(m.group(1)) if m else ""
    t = re.search(r"<title>(.*?)</title>", h, re.S)
    return {
        "title": htmlmod.unescape(t.group(1)).strip() if t else "",
        "description": meta("name", "description"),
        "ogTitle": meta("property", "og:title"),
        "ogDescription": meta("property", "og:description"),
    }


def contact_bullets(section):
    """Ricava i tre punti elenco (icona + testo) della sezione contatti."""
    out = []
    for li in re.findall(r"<li class=\"flex items-start gap-4\">(.*?)</li>", section, re.S):
        svg = re.search(r"<svg.*?</svg>", li, re.S)
        txt = re.search(r'<span class="text-lg[^"]*">(.*?)</span>', li, re.S)
        if svg and txt:
            out.append({"svg": svg.group(0), "text": htmlmod.unescape(txt.group(1)).strip()})
    return out


# ---------------------------------------------------------------- estrazione
home = read("home.html")
header_raw = clean(grab(home, r"<header.*?</header>"))
footer_raw = clean(grab(home, r"<footer.*?</footer>"))

contact_tpl = None
pages_data = []
for src, route, outfile in PAGES:
    h = read(src)
    main = grab(h, r"<main.*?</main>") or grab(h, r"<body[^>]*>(.*)</body>")
    contact = grab(h, r'<section id="contatti".*?</section>')
    if contact and contact_tpl is None:
        contact_tpl = clean(contact)
    body = clean(main)
    if contact:
        body = body.replace(clean(contact), "<!--CONTACT-->")
    pages_data.append({
        "route": route, "file": outfile, "body": body,
        "meta": head_meta(h),
        "bullets": contact_bullets(contact) if contact else None,
    })

os.makedirs(OUT, exist_ok=True)
json.dump({
    "header": header_raw,
    "footer": footer_raw,
    "contact": contact_tpl,
    "pages": pages_data,
}, open(os.path.join(OUT, "extracted.json"), "w"), indent=1, ensure_ascii=False)

print("header  :", len(header_raw), "byte")
print("footer  :", len(footer_raw), "byte")
print("contact :", len(contact_tpl or ""), "byte")
for p in pages_data:
    b = len(p["bullets"]) if p["bullets"] else 0
    print(f"{p['route']:28s} main {len(p['body']):6d} byte  bullet {b}  title: {p['meta']['title'][:50]}")
