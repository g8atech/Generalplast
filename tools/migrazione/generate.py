#!/usr/bin/env python3
"""
Genera i file sorgente Astro a partire dal markup estratto.
Strumento di migrazione: si esegue una volta, poi i .astro sono i sorgenti veri.
"""
import json, os, re, sys, html as htmlmod

EXTRACT = sys.argv[1]
ROOT = sys.argv[2]
PANEL = sys.argv[3]  # markup del menu mobile catturato dal sito live

d = json.load(open(os.path.join(EXTRACT, "extracted.json"), encoding="utf-8"))
mobile_panel = open(PANEL, encoding="utf-8").read()


def w(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(content.rstrip() + "\n")
    print(f"  {path}")


def fix_react(s):
    """Attributi in forma React -> HTML valido."""
    s = s.replace('autoComplete="off"', 'autocomplete="off"')
    s = s.replace('maxLength="2000"', 'maxlength="2000"')
    s = s.replace('charSet=', "charset=")
    s = re.sub(r'\srequired=""', " required", s)
    return s


# =============================================================== config
site_config = {
    "site": {"url": "https://generalplast.it", "lang": "it", "locale": "it_IT"},
    "brand": {
        "name": "GENERALPLAST",
        "legalName": "Generalplast Srl",
        "logo": "/logo.png",
        "logoAlt": "Generalplast",
        "footerText": "Dal 1968 stampaggio ed estrusione di articoli in plastica per l'edilizia civile, industriale e per il conto terzi.",
        "foundedYear": 1968,
        "credit": {"label": "G8A Technology SRL", "url": "https://www.g8a.it/"},
    },
    "contact": {
        "phone": "0331 217419",
        "phoneHref": "tel:+390331217419",
        "fax": "0331 216048",
        "email": "info@generalplast.it",
        "addressLine": "Via Giambello, 5 — 21040 Jerago con Orago (VA)",
        "street": "Via Giambello, 5",
        "postalCode": "21040",
        "city": "Jerago con Orago",
        "region": "VA",
        "country": "IT",
        "latitude": 45.7050391,
        "longitude": 8.8058676,
        "mapsUrl": "https://www.google.com/maps/search/?api=1&query=Google&query_place_id=ChIJcRD0gRqIhkcR32axAzWtuQs",
        "vat": "00213590128",
    },
    "form": {
        "provider": "web3forms",
        "accessKey": "03ebd183-25ee-4946-9b2c-9c887c3f3d0d",
        "subject": "Nuova richiesta dal sito Generalplast",
        "fromName": "Sito Generalplast",
        "successTitle": "Richiesta inviata",
        "successText": "Ti risponderemo al più presto.",
        "errorTitle": "Invio non riuscito",
        "errorText": "Riprova tra poco oppure chiamaci allo 0331 217419.",
        "sendingLabel": "Invio in corso…",
        "submitLabel": "Invia",
    },
    "nav": {
        "catalogUrl": "https://anyflip.com/rswwi/uyga",
    },
}
w("src/config/site.json", json.dumps(site_config, indent=2, ensure_ascii=False))

# =============================================================== tokens
w("src/styles/tokens.css", """/* Identità visiva del cliente.
   È l'unico file da toccare per ritingere il sito su un altro marchio. */
:root {
  --radius: 0.25rem;

  --background: oklch(100% 0 0);
  --foreground: oklch(19% 0.012 250);

  --primary: oklch(53% 0.221 27.5);
  --primary-foreground: oklch(99% 0 0);

  --muted: oklch(96% 0.004 250);
  --muted-foreground: oklch(50% 0.016 250);

  --steel: oklch(22% 0.014 250);
  --steel-foreground: oklch(98% 0 0);

  --border: oklch(92.9% 0.013 255.508);
  --input: oklch(92.9% 0.013 255.508);
  --ring: oklch(70.4% 0.04 256.788);

  --gradient-hero: linear-gradient(120deg, oklch(19% 0.012 250 / 0.92) 0%, oklch(19% 0.012 250 / 0.55) 55%, oklch(19% 0.012 250 / 0.25) 100%);
  --gradient-accent: linear-gradient(100deg, oklch(53% 0.221 27.5), oklch(62% 0.2 33));

  --shadow-card: 0 18px 45px -25px oklch(19% 0.012 250 / 0.55);
  --shadow-strong: 0 30px 70px -35px oklch(19% 0.012 250 / 0.7);
}""")

# =============================================================== global css
w("src/styles/global.css", """@import "tailwindcss";
@import "./tokens.css";

/* Mappatura dei token sul tema Tailwind. Parte condivisa del template. */
@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-steel: var(--steel);
  --color-steel-foreground: var(--steel-foreground);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);

  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-display: "Archivo", ui-sans-serif, system-ui, sans-serif;

  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
}

@layer base {
  *,
  ::before,
  ::after,
  ::backdrop {
    border-color: var(--border);
  }
  body {
    background-color: var(--color-background);
    color: var(--color-foreground);
    font-family: var(--font-sans);
  }
}

@utility container-page {
  width: 100%;
  max-width: 76rem;
  margin-inline: auto;
  padding-inline: 1.5rem;
}

@utility eyebrow {
  font-family: var(--font-display);
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--color-primary);
  font-size: 0.72rem;
  font-weight: 700;
}

/* Notifica di esito del form contatti. */
.toaster {
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  pointer-events: none;
}
.toast {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  width: 20rem;
  max-width: calc(100vw - 2rem);
  padding: 1rem;
  border-radius: calc(var(--radius) + 4px);
  border: 1px solid var(--border);
  background: var(--background);
  color: var(--foreground);
  box-shadow: var(--shadow-card);
  font-size: 0.8125rem;
  line-height: 1.4;
  opacity: 0;
  transform: translateY(0.75rem);
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.toast[data-show="1"] {
  opacity: 1;
  transform: translateY(0);
}
.toast strong {
  font-weight: 600;
}
.toast span {
  color: var(--muted-foreground);
}""")

# =============================================================== astro config
w("astro.config.mjs", """import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";
import site from "./src/config/site.json" with { type: "json" };

export default defineConfig({
  site: site.site.url,
  trailingSlash: "never",
  build: { format: "file" },
  vite: { plugins: [tailwindcss()] },
});""")

# =============================================================== header
header = fix_react(d["header"])
# il pannello mobile viene dal sito live: ripulisco gli attributi di stato
panel = fix_react(mobile_panel)
panel = re.sub(r'\s*data-status="active"', "", panel)
panel = re.sub(r'\s*aria-current="page"', "", panel)
panel = panel.replace(' tracking-[0.14em] active"', ' tracking-[0.14em]"')
panel = panel.replace("</header>", "")
# il pannello è nascosto finché non si apre
panel = panel.replace(
    '<div class="border-t border-border bg-background md:hidden">',
    '<div id="mobile-nav" class="border-t border-border bg-background md:hidden" hidden>',
    1,
)
# link attivi gestiti lato server
header = header.replace("</div></header>", "</div>__MOBILE__</header>")
header = header.replace("__MOBILE__", panel)

# marca i link di navigazione per lo stato attivo
header = header.replace(
    '[&amp;.active]:text-primary" href="/"',
    '[&amp;.active]:text-primary" data-nav="/" href="/"',
)
header = header.replace(
    '[&amp;.active]:text-primary" href="/stampaggio-conto-terzi"',
    '[&amp;.active]:text-primary" data-nav="/stampaggio-conto-terzi" href="/stampaggio-conto-terzi"',
)
header = header.replace('aria-label="Apri menu"', 'aria-label="Apri menu" aria-expanded="false" aria-controls="mobile-nav" id="mobile-toggle"')

w("src/components/Header.astro", """---
import site from "../config/site.json";
const path = Astro.url.pathname.replace(/\\/$/, "") || "/";
---
""" + header + """

<script>
  const toggle = document.getElementById("mobile-toggle");
  const panel = document.getElementById("mobile-nav");
  toggle?.addEventListener("click", () => {
    const open = panel?.hasAttribute("hidden");
    if (open) panel?.removeAttribute("hidden");
    else panel?.setAttribute("hidden", "");
    toggle.setAttribute("aria-expanded", String(open));
  });

  // stato attivo sui link di navigazione
  const here = location.pathname.replace(/\\/$/, "") || "/";
  document.querySelectorAll("[data-nav]").forEach((a) => {
    if (a.getAttribute("data-nav") === here) a.classList.add("active");
  });
</script>""")

# =============================================================== footer
footer = fix_react(d["footer"])
f = footer
f = f.replace("Copyright © 2026 GENERALPLAST. All rights reserved. Created by ",
              "Copyright © {new Date().getFullYear()} {site.brand.name}. All rights reserved. Created by ")
f = f.replace(">G8A Technology SRL<", ">{site.brand.credit.label}<")
f = f.replace('href="https://www.g8a.it/"', "href={site.brand.credit.url}")
f = f.replace("Via Giambello, 5 — 21040 Jerago con Orago (VA)", "{site.contact.addressLine}")
f = f.replace(">0331 217419<", ">{site.contact.phone}<")
f = f.replace('href="tel:+390331217419"', "href={site.contact.phoneHref}")
f = f.replace("FAX: 0331 216048", "FAX: {site.contact.fax}")
f = f.replace(">info@generalplast.it<", ">{site.contact.email}<")
f = f.replace('href="mailto:info@generalplast.it"', 'href={`mailto:${site.contact.email}`}')
f = f.replace("P.IVA 00213590128", "P.IVA {site.contact.vat}")
f = f.replace('href="https://www.google.com/maps/search/?api=1&amp;query=Google&amp;query_place_id=ChIJcRD0gRqIhkcR32axAzWtuQs"',
              "href={site.contact.mapsUrl}")
f = f.replace('src="/logo.png" alt="Generalplast"', "src={site.brand.logo} alt={site.brand.logoAlt}")
f = f.replace("Dal 1968 stampaggio ed estrusione di articoli in plastica per l&#x27;edilizia civile, industriale e per il conto terzi.",
              "{site.brand.footerText}")
w("src/components/Footer.astro", """---
import site from "../config/site.json";
---
""" + f)

# =============================================================== contatti
contact = fix_react(d["contact"])
# i tre punti elenco diventano una prop
bullets_block = re.search(r'<ul class="mt-10 space-y-6">.*?</ul>', contact, re.S).group(0)
contact = contact.replace(bullets_block, """<ul class="mt-10 space-y-6">{bullets.map((b) => (
  <li class="flex items-start gap-4">
    <span class="mt-0.5 grid size-10 shrink-0 place-items-center rounded-sm bg-[image:var(--gradient-accent)]"><Fragment set:html={b.svg} /></span>
    <span class="text-lg text-steel-foreground/85">{b.text}</span>
  </li>
))}</ul>""")
contact = contact.replace(">Invia<", ">{site.form.submitLabel}<")
contact = contact.replace("<form ", '<form id="contact-form" ')

w("src/components/ContactSection.astro", """---
import site from "../config/site.json";
interface Bullet { svg: string; text: string }
const { bullets } = Astro.props as { bullets: Bullet[] };
---
""" + contact + """

<div class="toaster" id="toaster" aria-live="polite"></div>

<script define:vars={{ cfg: site.form }}>
  const form = document.getElementById("contact-form");
  const toaster = document.getElementById("toaster");

  function toast(title, text) {
    const el = document.createElement("div");
    el.className = "toast";
    const t = document.createElement("strong");
    t.textContent = title;
    const s = document.createElement("span");
    s.textContent = text;
    el.append(t, s);
    toaster.append(el);
    requestAnimationFrame(() => el.setAttribute("data-show", "1"));
    setTimeout(() => {
      el.removeAttribute("data-show");
      setTimeout(() => el.remove(), 300);
    }, 5000);
  }

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const data = new FormData(form);
    const get = (k) => String(data.get(k) ?? "");

    btn.disabled = true;
    const label = btn.textContent;
    btn.textContent = cfg.sendingLabel;

    try {
      const res = await fetch("https://api.web3forms.com/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          access_key: cfg.accessKey,
          subject: cfg.subject,
          from_name: cfg.fromName,
          nome: get("nome"),
          azienda: get("azienda"),
          email: get("email"),
          telefono: get("telefono"),
          messaggio: get("messaggio"),
          replyto: get("email"),
          botcheck: get("botcheck"),
        }),
      });
      const json = await res.json().catch(() => null);
      if (json && json.success === true) {
        form.reset();
        toast(cfg.successTitle, cfg.successText);
      } else {
        throw new Error("invio fallito");
      }
    } catch {
      toast(cfg.errorTitle, cfg.errorText);
    } finally {
      btn.disabled = false;
      btn.textContent = label;
    }
  });
</script>""")

# =============================================================== layout
w("src/layouts/Base.astro", """---
import site from "../config/site.json";
import Header from "../components/Header.astro";
import Footer from "../components/Footer.astro";
import "../styles/global.css";

interface Props {
  title: string;
  description?: string;
  ogTitle?: string;
  ogDescription?: string;
  preload?: string[];
}
const { title, description, ogTitle, ogDescription, preload = [] } = Astro.props;
const canonical = new URL(Astro.url.pathname, site.site.url).href;
const org = {
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  name: site.brand.legalName,
  url: site.site.url,
  telephone: site.contact.phone,
  faxNumber: site.contact.fax,
  email: site.contact.email,
  vatID: site.contact.vat,
  foundingDate: String(site.brand.foundedYear),
  address: {
    "@type": "PostalAddress",
    streetAddress: site.contact.street,
    postalCode: site.contact.postalCode,
    addressLocality: site.contact.city,
    addressRegion: site.contact.region,
    addressCountry: site.contact.country,
  },
  geo: {
    "@type": "GeoCoordinates",
    latitude: site.contact.latitude,
    longitude: site.contact.longitude,
  },
};
---

<!doctype html>
<html lang={site.site.lang}>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="icon" href="/favicon.ico" type="image/x-icon" />
    <link rel="canonical" href={canonical} />
    <title>{title}</title>
    {description && <meta name="description" content={description} />}
    <meta property="og:type" content="website" />
    <meta property="og:locale" content={site.site.locale} />
    <meta property="og:url" content={canonical} />
    {ogTitle && <meta property="og:title" content={ogTitle} />}
    {ogDescription && <meta property="og:description" content={ogDescription} />}
    <meta property="og:image" content={new URL("/og.png", site.site.url).href} />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="author" content={site.brand.legalName} />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
    <link
      rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700;800;900&family=Inter:wght@400;500;600&display=swap"
    />
    {preload.map((href) => <link rel="preload" as="image" href={href} />)}
    <script type="application/ld+json" set:html={JSON.stringify(org)} />
  </head>
  <body>
    <div class="min-h-screen bg-background">
      <Header />
      <slot />
      <Footer />
    </div>
  </body>
</html>""")

# =============================================================== pagine
for p in d["pages"]:
    body = fix_react(p["body"])
    m = p["meta"]
    imgs = sorted(set(re.findall(r'<img src="(/[^"]+)"', body)))
    preload = [i for i in imgs if not i.endswith("logo.png")]
    uses_contact = "<!--CONTACT-->" in body
    if uses_contact:
        body = body.replace("<!--CONTACT-->", "<ContactSection bullets={bullets} />")
    front = ['---', 'import Base from "../layouts/Base.astro";']
    if uses_contact:
        front.append('import ContactSection from "../components/ContactSection.astro";')
        front.append("const bullets = " + json.dumps(p["bullets"], ensure_ascii=False, indent=2) + ";")
    front.append("---")
    attrs = [f'title={json.dumps(m["title"], ensure_ascii=False)}']
    if m["description"]:
        attrs.append(f'description={json.dumps(m["description"], ensure_ascii=False)}')
    if m["ogTitle"]:
        attrs.append(f'ogTitle={json.dumps(m["ogTitle"], ensure_ascii=False)}')
    if m["ogDescription"]:
        attrs.append(f'ogDescription={json.dumps(m["ogDescription"], ensure_ascii=False)}')
    if preload:
        attrs.append("preload={" + json.dumps(preload) + "}")
    open_tag = "<Base\n  " + "\n  ".join(attrs) + "\n>"
    w("src/pages/" + p["file"], "\n".join(front) + "\n\n" + open_tag + "\n" + body + "\n</Base>")

# =============================================================== robots + sitemap
w("src/pages/robots.txt.ts", """import type { APIRoute } from "astro";
import site from "../config/site.json";

export const GET: APIRoute = () =>
  new Response(
    `User-agent: *\\nAllow: /\\n\\nSitemap: ${new URL("/sitemap.xml", site.site.url).href}\\n`,
    { headers: { "Content-Type": "text/plain; charset=utf-8" } },
  );""")

w("src/pages/sitemap.xml.ts", """import type { APIRoute } from "astro";
import site from "../config/site.json";

const routes = ["/", "/lavorazione-produzione", "/stampaggio-conto-terzi", "/privacy"];

export const GET: APIRoute = () => {
  const now = new Date().toISOString().slice(0, 10);
  const urls = routes
    .map((r) => {
      const loc = new URL(r, site.site.url).href;
      const priority = r === "/" ? "1.0" : r === "/privacy" ? "0.3" : "0.8";
      return `  <url><loc>${loc}</loc><lastmod>${now}</lastmod><priority>${priority}</priority></url>`;
    })
    .join("\\n");
  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>\\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\\n${urls}\\n</urlset>\\n`,
    { headers: { "Content-Type": "application/xml; charset=utf-8" } },
  );
};""")

# =============================================================== vercel.json
w("vercel.json", json.dumps({
    "headers": [{
        "source": "/(.*)",
        "has": [{"type": "host", "value": "(.*)\\.vercel\\.app"}],
        "headers": [{"key": "X-Robots-Tag", "value": "noindex"}],
    }],
    "redirects": [
        {"source": "/homepage", "destination": "/", "permanent": True},
    ],
}, indent=2))

print("\nFatto.")
