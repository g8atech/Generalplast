// Controlla il contrasto fra testo e sfondo sulle combinazioni reali del sito.
//
//   npm run build && node tools/contrasto.cjs
//   SITO=https://generalplast.it node tools/contrasto.cjs
//
// I colori sono dichiarati in oklch: getComputedStyle li restituisce in quel
// formato, non in rgb. Per convertirli si usa il browser stesso, dipingendo
// il colore su una tela e rileggendone i byte — così qualunque formato CSS
// presente o futuro viene risolto correttamente.
const { chromium } = require("playwright-core");
const http = require("http");
const fs = require("fs");
const path = require("path");

const DIST = path.join(__dirname, "..", "dist");
const PORTA = 4471;
const SITO = process.env.SITO;
const PAGINE = (process.env.PAGINE || "/,/lavorazione-produzione,/stampaggio-conto-terzi,/privacy,/404").split(",");

const MIME = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".webp": "image/webp",
  ".png": "image/png", ".jpg": "image/jpeg", ".ico": "image/x-icon", ".woff2": "font/woff2" };

let srv = null;
if (!SITO) {
  srv = http.createServer((q, r) => {
    const p = q.url.split("?")[0];
    const c = path.extname(p) ? [path.join(DIST, p)]
      : [path.join(DIST, p, "index.html"), path.join(DIST, p + ".html")];
    const f = c.find((x) => fs.existsSync(x));
    if (!f) { r.writeHead(404); return r.end(); }
    r.writeHead(200, { "Content-Type": MIME[path.extname(f)] || "application/octet-stream" });
    fs.createReadStream(f).pipe(r);
  }).listen(PORTA);
}
const base = SITO || `http://localhost:${PORTA}`;

(async () => {
  const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
  const page = await b.newPage({ viewport: { width: 1280, height: 900 } });
  let totale = 0;

  for (const rotta of PAGINE) {
    await page.goto(base + rotta, { waitUntil: "networkidle", timeout: 60000 });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(400);

    const bassi = await page.evaluate(() => {
      const tela = document.createElement("canvas");
      tela.width = tela.height = 1;
      const ctx = tela.getContext("2d", { willReadFrequently: true });
      const cache = new Map();
      const aRgb = (c) => {
        if (cache.has(c)) return cache.get(c);
        ctx.clearRect(0, 0, 1, 1);
        ctx.fillStyle = "#000";
        ctx.fillStyle = c;
        ctx.fillRect(0, 0, 1, 1);
        const d = ctx.getImageData(0, 0, 1, 1).data;
        const v = [d[0], d[1], d[2], d[3] / 255];
        cache.set(c, v);
        return v;
      };
      const lum = ([r, g, b]) => {
        const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
      };
      // fondo effettivo: risale finché non trova un colore opaco
      const fondo = (el) => {
        let n = el;
        while (n && n !== document.documentElement) {
          const [r, g, b, a] = aRgb(getComputedStyle(n).backgroundColor);
          if (a > 0.95) return [r, g, b];
          n = n.parentElement;
        }
        return [255, 255, 255];
      };
      // Testo sopra una foto o una velatura: il contrasto dipende
      // dall'immagine, non dai colori del tema, e va giudicato a occhio.
      const sopraImmagine = (el) => {
        let n = el;
        while (n && n !== document.body) {
          const st = getComputedStyle(n);
          if (st.backgroundImage !== "none") return true;
          const padre = n.parentElement;
          if (padre) {
            for (const f of padre.children) {
              if (f === n) continue;
              const sf = getComputedStyle(f);
              if (sf.position !== "absolute") continue;
              if (f.tagName === "IMG" || sf.backgroundImage !== "none") return true;
            }
          }
          n = padre;
        }
        return false;
      };

      const out = [];
      for (const el of document.querySelectorAll("p,h1,h2,h3,h4,a,span,li,label,button,strong")) {
        const t = el.textContent.trim();
        if (!t || t.length < 3) continue;
        if ([...el.children].some((c) => c.textContent.trim())) continue;
        const st = getComputedStyle(el);
        if (st.display === "none" || st.visibility === "hidden" || +st.opacity === 0) continue;
        const r = el.getBoundingClientRect();
        if (!r.width || !r.height) continue;
        if (sopraImmagine(el)) continue;   // il contrasto dipende dalla foto, non dal tema

        const col = aRgb(st.color);
        const cr = (() => {
          const l1 = lum(col), l2 = lum(fondo(el));
          return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
        })();
        const px = parseFloat(st.fontSize);
        const grande = px >= 24 || (px >= 18.66 && +st.fontWeight >= 700);
        const soglia = grande ? 3 : 4.5;
        if (cr < soglia) out.push({ t: t.slice(0, 46), cr: cr.toFixed(2), soglia, px: Math.round(px) });
      }
      return out;
    });

    const unici = [...new Map(bassi.map((x) => [x.t, x])).values()];
    totale += unici.length;
    console.log(`   ${rotta.padEnd(26)} ${unici.length ? unici.length + " sotto soglia" : "a norma"}`);
    unici.slice(0, 6).forEach((x) =>
      console.log(`      "${x.t}" — ${x.cr}:1 (serve ${x.soglia}:1, ${x.px}px)`));
  }

  await b.close();
  if (srv) srv.close();
  console.log(totale === 0
    ? "\n   Contrasto conforme ovunque (testo su foto escluso: dipende dall'immagine)."
    : `\n   ${totale} elementi con contrasto insufficiente`);
  process.exit(totale ? 1 : 0);
})();
