// Verifica le parti interattive: form contatti, menu mobile, tendina prodotti.
// La chiamata a Web3Forms viene intercettata: il controllo è sul contenuto
// inviato, non sulla consegna della mail.
const { chromium } = require("playwright-core");
const http = require("http");
const fs = require("fs");
const path = require("path");

const DIST = path.join(__dirname, "..", "dist");
const PORT = 4410;
const MIME = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".png": "image/png", ".jpg": "image/jpeg", ".gif": "image/gif", ".ico": "image/x-icon", ".xml": "application/xml", ".txt": "text/plain" };

const srv = http.createServer((q, r) => {
  const p = q.url.split("?")[0];
  // Risolve come Vercel: prima la cartella, poi il file .html.
  const candidates = path.extname(p)
    ? [path.join(DIST, p)]
    : [path.join(DIST, p, "index.html"), path.join(DIST, p + ".html")];
  const f = candidates.find((x) => fs.existsSync(x));
  if (!f) { r.writeHead(404); return r.end(); }
  r.writeHead(200, { "Content-Type": MIME[path.extname(f)] || "application/octet-stream" });
  fs.createReadStream(f).pipe(r);
}).listen(PORT);

const base = `http://localhost:${PORT}`;
let fails = 0;
const ok = (c, m, extra = "") => { console.log(`  ${c ? "ok  " : "NO  "}${m}${extra ? "  — " + extra : ""}`); if (!c) fails++; };

async function fill(page) {
  await page.fill('input[name="nome"]', "Mario Rossi");
  await page.fill('input[name="azienda"]', "Acme Srl");
  await page.fill('input[name="email"]', "mario@acme.it");
  await page.fill('input[name="telefono"]', "0331 000000");
  await page.fill('textarea[name="messaggio"]', "Richiesta di preventivo per profili in PVC.");
}

(async () => {
  const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });

  // ---------------------------------------------- 1. invio riuscito
  console.log("Form contatti — invio riuscito");
  {
    const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
    let payload = null;
    await p.route("https://api.web3forms.com/submit", (route) => {
      payload = JSON.parse(route.request().postData() || "{}");
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ success: true, message: "ok" }) });
    });
    await p.goto(base + "/");
    await fill(p);
    await p.check('input[name="privacy"]');
    await p.click('#contact-form button[type="submit"]');
    await p.waitForTimeout(900);

    ok(!!payload, "la richiesta parte verso Web3Forms");
    if (payload) {
      ok(/^[0-9a-f-]{36}$/.test(payload.access_key || ""), "access key presente", payload.access_key);
      ok(payload.nome === "Mario Rossi" && payload.email === "mario@acme.it", "i campi compilati vengono inviati");
      ok(payload.azienda === "Acme Srl" && payload.telefono === "0331 000000", "azienda e telefono inclusi");
      ok((payload.messaggio || "").startsWith("Richiesta"), "messaggio incluso");
      ok(payload.replyto === "mario@acme.it", "reply-to impostato su chi compila");
      ok(!!payload.subject && !!payload.from_name, "oggetto e mittente impostati", payload.subject);
      ok("botcheck" in payload, "campo honeypot inviato");
    }
    const toast = await p.textContent("#toaster").catch(() => "");
    ok((toast || "").includes("Richiesta inviata"), "conferma mostrata solo dopo risposta positiva");
    const nome = await p.inputValue('input[name="nome"]');
    ok(nome === "", "il modulo viene svuotato dopo l'invio");
    await p.close();
  }

  // ---------------------------------------------- 2. errore del servizio
  console.log("\nForm contatti — servizio che risponde male");
  {
    const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
    await p.route("https://api.web3forms.com/submit", (route) =>
      route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ success: false }) }));
    await p.goto(base + "/");
    await fill(p);
    await p.check('input[name="privacy"]');
    await p.click('#contact-form button[type="submit"]');
    await p.waitForTimeout(900);
    const toast = (await p.textContent("#toaster")) || "";
    ok(toast.includes("Invio non riuscito"), "viene mostrato l'errore");
    ok(!toast.includes("Richiesta inviata"), "NON viene mostrata una falsa conferma");
    ok((await p.inputValue('input[name="nome"]')) === "Mario Rossi", "i dati restano nel modulo per riprovare");
    const disabled = await p.getAttribute('#contact-form button[type="submit"]', "disabled");
    ok(disabled === null, "il pulsante torna attivo");
    await p.close();
  }

  // ---------------------------------------------- 3. consenso privacy
  console.log("\nForm contatti — consenso privacy obbligatorio");
  {
    const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
    let called = false;
    await p.route("https://api.web3forms.com/submit", (route) => { called = true; return route.fulfill({ status: 200, body: "{}" }); });
    await p.goto(base + "/");
    await fill(p);
    await p.click('#contact-form button[type="submit"]');
    await p.waitForTimeout(600);
    ok(!called, "senza spunta privacy non parte nulla");
    await p.close();
  }

  // ---------------------------------------------- 4. menu mobile
  console.log("\nMenu mobile");
  {
    const p = await b.newPage({ viewport: { width: 390, height: 844 } });
    await p.goto(base + "/");
    ok(!(await p.isVisible("#mobile-nav")), "chiuso all'apertura della pagina");
    await p.click("#mobile-toggle");
    await p.waitForTimeout(300);
    ok(await p.isVisible("#mobile-nav"), "si apre al tocco");
    ok((await p.getAttribute("#mobile-toggle", "aria-expanded")) === "true", "stato accessibile aggiornato");
    const links = await p.$$eval("#mobile-nav a", (a) => a.map((x) => x.getAttribute("href")));
    ok(links.includes("/lavorazione-produzione") && links.includes("/stampaggio-conto-terzi"), "contiene i link di navigazione", links.length + " link");
    await p.click("#mobile-toggle");
    await p.waitForTimeout(300);
    ok(!(await p.isVisible("#mobile-nav")), "si richiude");
    await p.close();
  }

  // ---------------------------------------------- 5. tendina prodotti
  console.log("\nTendina «Prodotti edilizia» (desktop)");
  {
    const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
    await p.goto(base + "/");
    const dd = p.locator("header nav .group .invisible, header nav .group > div").last();
    await p.hover("header nav .group button");
    await p.waitForTimeout(400);
    ok(await dd.isVisible(), "si apre al passaggio del mouse");
    const hrefs = await p.$$eval("header nav .group a", (a) => a.map((x) => x.getAttribute("href")));
    ok(hrefs.some((h) => h && h.includes("anyflip")), "il link al catalogo è presente");
    await p.close();
  }

  // ---------------------------------------------- 6. stato attivo e pagine
  console.log("\nNavigazione");
  {
    const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
    for (const r of ["/", "/lavorazione-produzione", "/stampaggio-conto-terzi", "/privacy"]) {
      const res = await p.goto(base + r);
      ok(res.status() === 200, `pagina ${r} raggiungibile`);
    }
    await p.goto(base + "/stampaggio-conto-terzi");
    await p.waitForTimeout(300);
    const active = await p.$$eval("header nav a.active", (a) => a.map((x) => x.getAttribute("href")));
    ok(active.includes("/stampaggio-conto-terzi"), "il link della pagina corrente è evidenziato");
    await p.close();
  }

  await b.close();
  srv.close();
  console.log(`\n${fails === 0 ? "Tutti i controlli superati." : fails + " CONTROLLI FALLITI"}`);
  process.exit(fails ? 1 : 0);
})();
