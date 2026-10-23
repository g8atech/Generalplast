// Confronta il testo visibile fra il sito di riferimento e il nostro,
// pagina per pagina. Il confronto a schermate non basta: se il sito di
// riferimento cambia dopo la copia, le differenze di testo vanno trovate qui.
const { chromium } = require("playwright-core");

const REF = process.env.REF;  // indirizzo di riferimento, obbligatorio
const MINE = process.env.MINE;  // indirizzo da controllare, obbligatorio
const ROUTES = (process.env.ROUTES || "/,/lavorazione-produzione,/stampaggio-conto-terzi").split(",");

async function textOf(page, url) {
  await page.goto(url, { waitUntil: "networkidle", timeout: 90000 });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(500);
  return page.evaluate(() => {
    const out = [];
    const walk = (node) => {
      for (const child of node.childNodes) {
        if (child.nodeType === 3) {
          const t = child.textContent.replace(/\s+/g, " ").trim();
          if (t) out.push(t);
        } else if (child.nodeType === 1) {
          const s = getComputedStyle(child);
          if (s.display === "none" || s.visibility === "hidden") continue;
          walk(child);
        }
      }
    };
    walk(document.body);
    return out;
  });
}

// Differenza riga per riga, con allineamento (Myers semplificato via LCS).
function lcsDiff(a, b) {
  const n = a.length, m = b.length;
  const dp = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
  for (let i = n - 1; i >= 0; i--)
    for (let j = m - 1; j >= 0; j--)
      dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  const ops = [];
  let i = 0, j = 0;
  while (i < n && j < m) {
    if (a[i] === b[j]) { ops.push(["=", a[i]]); i++; j++; }
    else if (dp[i + 1][j] >= dp[i][j + 1]) { ops.push(["-", a[i]]); i++; }
    else { ops.push(["+", b[j]]); j++; }
  }
  while (i < n) ops.push(["-", a[i++]]);
  while (j < m) ops.push(["+", b[j++]]);
  return ops;
}

(async () => {
  if (!REF || !MINE) {
    console.error("Servono REF e MINE: REF=https://riferimento MINE=https://nostro node tools/diff-testi.cjs");
    process.exit(2);
  }
  const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
  const page = await (await b.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  let totale = 0;

  for (const route of ROUTES) {
    const ref = await textOf(page, REF + route);
    const mine = await textOf(page, MINE + route);
    const ops = lcsDiff(ref, mine);
    const diffs = ops.filter(([k]) => k !== "=");
    console.log(`\n=== ${route} ===  riferimento ${ref.length} frammenti, nostro ${mine.length}`);
    if (!diffs.length) { console.log("  nessuna differenza di testo"); continue; }
    totale += diffs.length;
    ops.forEach(([k, t], idx) => {
      if (k === "=") return;
      const ctx = ops[idx - 1] && ops[idx - 1][0] === "=" ? ops[idx - 1][1].slice(0, 42) : "";
      const seg = t.length > 100 ? t.slice(0, 100) + "…" : t;
      console.log(`  ${k === "-" ? "SITO APPROVATO" : "NOSTRO        "}  ${seg}${ctx ? `\n                    (dopo: "${ctx}")` : ""}`);
    });
  }

  await b.close();
  console.log(`\n${totale === 0 ? "Testi allineati." : totale + " differenze di testo da sistemare"}`);
  process.exit(totale ? 1 : 0);
})();
