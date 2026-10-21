// Confronta il sito ricostruito con quello live, schermata per schermata.
const { chromium } = require("playwright-core");
const http = require("http");
const fs = require("fs");
const path = require("path");

const DIST = path.join(__dirname, "..", "dist");
const OUT = process.env.OUT || "/tmp/cmp";
const LIVE = process.env.LIVE || "https://plastic-reimagined-modern.vercel.app";
// Con NEW si confronta un deploy remoto invece della build locale.
const NEW = process.env.NEW || null;
const PORT = 4399;

const ROUTES = ["/", "/lavorazione-produzione", "/stampaggio-conto-terzi", "/privacy"];
const VIEWPORTS = [
  { name: "desktop", width: 1280, height: 900 },
  { name: "mobile", width: 390, height: 844 },
];

const MIME = {
  ".html": "text/html", ".css": "text/css", ".js": "text/javascript",
  ".png": "image/png", ".jpg": "image/jpeg", ".gif": "image/gif",
  ".ico": "image/x-icon", ".xml": "application/xml", ".txt": "text/plain",
};

function serve() {
  return http.createServer((req, res) => {
    const p = decodeURIComponent(req.url.split("?")[0]);
    // Risolve come Vercel: prima la cartella, poi il file .html.
    const candidates = path.extname(p)
      ? [path.join(DIST, p)]
      : [path.join(DIST, p, "index.html"), path.join(DIST, p + ".html")];
    const file = candidates.find((f) => fs.existsSync(f));
    if (!file) { res.writeHead(404); return res.end("404"); }
    res.writeHead(200, { "Content-Type": MIME[path.extname(file)] || "application/octet-stream" });
    fs.createReadStream(file).pipe(res);
  }).listen(PORT);
}

// Congela le gif e disattiva le transizioni: altrimenti il confronto
// misura l'animazione, non il layout.
const FREEZE = `*,*::before,*::after{animation:none!important;transition:none!important}`;

// Le gif animate non si fermano: le loro aree vengono escluse dal confronto,
// con le coordinate lette dal DOM. I file sono gli stessi su entrambi i lati.
const GIF_BOXES = {};

async function shoot(page, url, file) {
  await page.goto(url, { waitUntil: "networkidle", timeout: 90000 });
  await page.addStyleTag({ content: FREEZE });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(900);
  await page.evaluate(async () => {
    // forza il caricamento pigro scorrendo tutta la pagina
    await new Promise((r) => {
      let y = 0;
      const step = () => {
        y += window.innerHeight;
        window.scrollTo(0, y);
        if (y < document.body.scrollHeight) setTimeout(step, 60);
        else { window.scrollTo(0, 0); setTimeout(r, 250); }
      };
      step();
    });
  });
  await page.waitForTimeout(400);
  const boxes = await page.evaluate(() =>
    [...document.querySelectorAll('img[src$=".gif"]')].map((i) => {
      const r = i.getBoundingClientRect();
      return [
        Math.floor(r.left + window.scrollX) - 2,
        Math.floor(r.top + window.scrollY) - 2,
        Math.ceil(r.right + window.scrollX) + 2,
        Math.ceil(r.bottom + window.scrollY) + 2,
      ];
    }),
  );
  await page.screenshot({ path: file, fullPage: true });
  return boxes;
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const server = serve();
  const browser = await chromium.launch({
    executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
  });

  for (const vp of VIEWPORTS) {
    const ctx = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: 1,
      reducedMotion: "reduce",
    });
    const page = await ctx.newPage();
    for (const route of ROUTES) {
      const slug = route === "/" ? "home" : route.slice(1);
      const key = `${slug}.${vp.name}`;
      const a = await shoot(page, LIVE + route, `${OUT}/${key}.live.png`);
      const b = await shoot(page, (NEW || `http://localhost:${PORT}`) + route, `${OUT}/${key}.new.png`);
      GIF_BOXES[key] = [...a, ...b];
      console.log(`ok ${key}  (aree gif escluse: ${a.length})`);
    }
    await ctx.close();
  }

  fs.writeFileSync(`${OUT}/gif-boxes.json`, JSON.stringify(GIF_BOXES, null, 1));
  await browser.close();
  server.close();
})();
