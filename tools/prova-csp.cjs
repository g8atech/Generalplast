// Serve il sito costruito applicando le intestazioni di vercel.json e
// controlla che nulla venga bloccato: una politica di sicurezza sbagliata
// rompe il form in silenzio, e in produzione te ne accorgi dai lead mancanti.
const { chromium } = require("playwright-core");
const http = require("http");
const fs = require("fs");
const path = require("path");

const RADICE = path.join(__dirname, "..");
const DIST = path.join(RADICE, "dist");
const PORTA = 4460;
const conf = JSON.parse(fs.readFileSync(path.join(RADICE, "vercel.json"), "utf8"));

const MIME = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript",
  ".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg", ".ico": "image/x-icon",
  ".woff2": "font/woff2", ".xml": "application/xml", ".txt": "text/plain" };

// le intestazioni valide per tutto il sito, escluse quelle legate all'anteprima
const comuni = conf.headers
  .filter((h) => h.source === "/(.*)" && !h.has)
  .flatMap((h) => h.headers);

const srv = http.createServer((q, r) => {
  const p = decodeURIComponent(q.url.split("?")[0]);
  const cand = path.extname(p) ? [path.join(DIST, p)]
    : [path.join(DIST, p, "index.html"), path.join(DIST, p + ".html")];
  const f = cand.find((x) => fs.existsSync(x));
  if (!f) { r.writeHead(404); return r.end("404"); }
  const h = { "Content-Type": MIME[path.extname(f)] || "application/octet-stream" };
  for (const { key, value } of comuni) h[key] = value;
  r.writeHead(200, h);
  fs.createReadStream(f).pipe(r);
}).listen(PORTA);

const base = `http://localhost:${PORTA}`;
let problemi = 0;

(async () => {
  console.log("Intestazioni applicate:");
  comuni.forEach((h) => console.log(`   ${h.key}`));

  const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  const violazioni = [];
  page.on("console", (m) => {
    const t = m.text();
    if (/Content Security Policy|Refused to/i.test(t)) violazioni.push(t);
  });

  console.log("\nPagine:");
  for (const r of ["/", "/lavorazione-produzione", "/stampaggio-conto-terzi", "/privacy"]) {
    await page.goto(base + r, { waitUntil: "networkidle", timeout: 60000 });
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate(async () => {
      await new Promise((res) => { let y = 0; const s = () => { y += innerHeight; scrollTo(0, y);
        if (y < document.body.scrollHeight) setTimeout(s, 50); else res(); }; s(); });
    });
    await page.waitForTimeout(600);
    const stato = await page.evaluate(() => ({
      immaginiRotte: [...document.querySelectorAll("img")].filter((i) => i.naturalWidth === 0).length,
      carattere: getComputedStyle(document.querySelector("h1") || document.body).fontFamily,
      stiliApplicati: getComputedStyle(document.body).backgroundColor !== "rgba(0, 0, 0, 0)",
    }));
    const ok = stato.immaginiRotte === 0 && /Archivo/.test(stato.carattere) && stato.stiliApplicati;
    console.log(`   ${ok ? "·" : "✗"} ${r}  immagini rotte: ${stato.immaginiRotte}, carattere: ${stato.carattere.split(",")[0]}`);
    if (!ok) problemi++;
  }

  console.log("\nForm contatti con la politica attiva:");
  let inviato = null;
  await page.route("https://api.web3forms.com/submit", (route) => {
    inviato = JSON.parse(route.request().postData() || "{}");
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ success: true }) });
  });
  await page.goto(base + "/", { waitUntil: "networkidle" });
  await page.fill('input[name="nome"]', "Prova");
  await page.fill('input[name="email"]', "prova@esempio.it");
  await page.fill('textarea[name="messaggio"]', "Verifica delle intestazioni di sicurezza.");
  await page.check('input[name="privacy"]');
  await page.click('#contact-form button[type="submit"]');
  await page.waitForTimeout(1200);
  if (inviato && inviato.access_key) console.log("   · la richiesta raggiunge Web3Forms");
  else { console.log("   ✗ la richiesta NON parte: la politica blocca la chiamata"); problemi++; }
  const toast = (await page.textContent("#toaster")) || "";
  toast.includes("inviata") ? console.log("   · conferma mostrata") : (console.log("   ✗ nessuna conferma"), problemi++);

  console.log("\nViolazioni della politica:");
  if (violazioni.length === 0) console.log("   · nessuna");
  else { violazioni.slice(0, 8).forEach((v) => console.log(`   ✗ ${v.slice(0, 130)}`)); problemi += violazioni.length; }

  await b.close();
  srv.close();
  console.log(`\n${problemi === 0 ? "Le intestazioni non rompono nulla." : problemi + " problemi"}`);
  process.exit(problemi ? 1 : 0);
})();
