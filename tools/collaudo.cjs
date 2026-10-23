// Collaudo del sito pubblicato: risorse, link, SEO, accessibilità.
// Si esegue sul dominio vero prima della consegna.
//
//   SITO=https://generalplast.it node tools/collaudo.cjs
const { chromium } = require("playwright-core");

const SITO = process.env.SITO;
if (!SITO) {
  console.error("Serve SITO, es. SITO=https://generalplast.it node tools/collaudo.cjs");
  process.exit(2);
}
const PAGINE = (process.env.PAGINE || "/,/lavorazione-produzione,/stampaggio-conto-terzi,/privacy").split(",");

let problemi = 0;
const no = (m, d = "") => { console.log(`  ✗ ${m}${d ? "  — " + d : ""}`); problemi++; };
const si = (m, d = "") => console.log(`  · ${m}${d ? "  — " + d : ""}`);

(async () => {
  const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  const falliti = new Map();
  page.on("response", (r) => {
    if (r.status() >= 400) falliti.set(r.url(), r.status());
  });
  const erroriJs = [];
  page.on("pageerror", (e) => erroriJs.push(e.message));
  page.on("console", (m) => { if (m.type() === "error") erroriJs.push(m.text()); });

  const linkEsterni = new Set();
  const titoliPerPagina = {};

  for (const rotta of PAGINE) {
    console.log(`\n=== ${rotta} ===`);
    const res = await page.goto(SITO + rotta, { waitUntil: "networkidle", timeout: 90000 });
    if (res.status() !== 200) { no("la pagina non risponde", String(res.status())); continue; }
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate(async () => {
      await new Promise((r) => { let y = 0; const s = () => { y += innerHeight; scrollTo(0, y);
        if (y < document.body.scrollHeight) setTimeout(s, 50); else { scrollTo(0, 0); setTimeout(r, 400); } }; s(); });
    });

    const d = await page.evaluate(() => {
      const meta = (sel) => document.querySelector(sel)?.content || "";
      return {
        titolo: document.title,
        descrizione: meta('meta[name="description"]'),
        canonico: document.querySelector('link[rel="canonical"]')?.href || "",
        ogTitolo: meta('meta[property="og:title"]'),
        ogImg: meta('meta[property="og:image"]'),
        lang: document.documentElement.lang,
        h1: [...document.querySelectorAll("h1")].map((h) => h.textContent.trim()),
        titoli: [...document.querySelectorAll("h1,h2,h3,h4")].map((h) => +h.tagName[1]),
        imgSenzaAlt: [...document.querySelectorAll("img")].filter((i) => !i.getAttribute("alt")).length,
        imgRotte: [...document.querySelectorAll("img")].filter((i) => i.naturalWidth === 0).map((i) => i.getAttribute("src")),
        linkVuoti: [...document.querySelectorAll("a")].filter((a) => !a.textContent.trim() && !a.querySelector("img") && !a.getAttribute("aria-label")).length,
        esterni: [...document.querySelectorAll('a[href^="http"]')]
          .filter((a) => !a.href.startsWith(location.origin))
          .map((a) => ({ href: a.href, blank: a.target === "_blank", rel: a.rel })),
        interni: [...document.querySelectorAll("a[href]")]
          .map((a) => a.getAttribute("href")).filter((h) => h && h.startsWith("/")),
        ld: [...document.querySelectorAll('script[type="application/ld+json"]')].map((s) => s.textContent),
        campi: [...document.querySelectorAll("input,textarea,select")]
          .filter((i) => i.type !== "hidden" && i.type !== "checkbox")
          .map((i) => ({ name: i.name, etichetta: !!(i.labels && i.labels.length) || !!i.getAttribute("aria-label") })),
      };
    });

    titoliPerPagina[rotta] = d;

    d.titolo && d.titolo.length <= 65 ? si("titolo", `${d.titolo.length} caratteri`)
      : no("titolo assente o troppo lungo", `${d.titolo.length} caratteri`);
    d.descrizione && d.descrizione.length >= 70 && d.descrizione.length <= 170
      ? si("descrizione", `${d.descrizione.length} caratteri`)
      : no("descrizione assente o fuori misura", `${d.descrizione.length} caratteri`);
    d.canonico ? si("indirizzo canonico", d.canonico) : no("indirizzo canonico assente");
    d.lang === "it" ? si("lingua dichiarata") : no("lingua non dichiarata", d.lang || "vuota");
    d.h1.length === 1 ? si("un solo H1", d.h1[0].slice(0, 46)) : no(`H1 presenti: ${d.h1.length}`);

    let salti = [];
    for (let i = 1; i < d.titoli.length; i++)
      if (d.titoli[i] - d.titoli[i - 1] > 1) salti.push(`h${d.titoli[i - 1]}→h${d.titoli[i]}`);
    salti.length ? no("gerarchia dei titoli con salti", salti.slice(0, 3).join(", ")) : si("gerarchia dei titoli coerente");

    d.imgSenzaAlt === 0 ? si("tutte le immagini hanno testo alternativo") : no(`${d.imgSenzaAlt} immagini senza testo alternativo`);
    d.imgRotte.length === 0 ? si("nessuna immagine rotta") : no("immagini che non caricano", d.imgRotte.join(", "));
    d.linkVuoti === 0 ? si("nessun link senza testo") : no(`${d.linkVuoti} link senza testo né etichetta`);

    const senzaEtichetta = d.campi.filter((c) => !c.etichetta);
    if (d.campi.length) senzaEtichetta.length === 0
      ? si(`${d.campi.length} campi del modulo, tutti con etichetta`)
      : no("campi senza etichetta", senzaEtichetta.map((c) => c.name).join(", "));

    for (const t of d.ld) {
      try { const j = JSON.parse(t); si("dati strutturati validi", j["@type"]); }
      catch { no("dati strutturati non leggibili"); }
    }

    for (const e of d.esterni) linkEsterni.add(JSON.stringify(e));
    for (const i of d.interni) {
      if (i.startsWith("/") && !i.startsWith("//") && !PAGINE.includes(i.split("#")[0]) && i !== "/" && !i.startsWith("/#")) {
        const u = SITO + i.split("#")[0];
        const r = await page.request.get(u).catch(() => null);
        if (!r || r.status() >= 400) no("link interno rotto", i);
      }
    }
  }

  console.log("\n=== link esterni ===");
  for (const s of linkEsterni) {
    const e = JSON.parse(s);
    const r = await page.request.get(e.href, { timeout: 25000 }).catch(() => null);
    const stato = r ? r.status() : "irraggiungibile";
    const sicuro = !e.blank || /noopener|noreferrer/.test(e.rel);
    if (!r || r.status() >= 400) no("link esterno non raggiungibile", `${e.href} (${stato})`);
    else si(`${e.href}`, `${stato}${sicuro ? "" : "  ATTENZIONE: target _blank senza rel noopener"}`);
    if (!sicuro) problemi++;
  }

  console.log("\n=== varie ===");
  falliti.size === 0 ? si("nessuna richiesta fallita") : [...falliti].forEach(([u, s]) => no("risorsa non trovata", `${s} ${u}`));
  erroriJs.length === 0 ? si("nessun errore in console") : erroriJs.slice(0, 5).forEach((e) => no("errore in console", e.slice(0, 110)));

  const titoli = Object.values(titoliPerPagina).map((d) => d.titolo);
  new Set(titoli).size === titoli.length ? si("titoli tutti diversi fra le pagine") : no("titoli duplicati fra pagine");
  const desc = Object.values(titoliPerPagina).map((d) => d.descrizione);
  new Set(desc).size === desc.length ? si("descrizioni tutte diverse") : no("descrizioni duplicate fra pagine");

  await b.close();
  console.log(`\n${problemi === 0 ? "Nessun problema." : problemi + " cose da sistemare"}`);
  process.exit(problemi ? 1 : 0);
})();
