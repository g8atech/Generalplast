// Verifica che le modifiche chieste dal cliente siano effettivamente a posto
// nel sito costruito. La lista sta in tools/richieste-cliente.json e si
// riscrive per ogni cliente a partire dal suo elenco di richieste.
const fs = require("fs");
const path = require("path");

const DIST = path.join(__dirname, "..", "dist");
const lista = JSON.parse(fs.readFileSync(path.join(__dirname, "richieste-cliente.json"), "utf8"));

// Testo visibile della pagina, senza marcatura: così il confronto non
// dipende da come il markup è spezzato.
function testoDi(route, zona) {
  const file = route === "/" ? path.join(DIST, "index.html") : path.join(DIST, route, "index.html");
  if (!fs.existsSync(file)) return null;
  let h = fs.readFileSync(file, "utf8");
  h = h.replace(/<script[\s\S]*?<\/script>/g, " ").replace(/<style[\s\S]*?<\/style>/g, " ");
  // "zona" limita il controllo a una parte della pagina: serve quando una
  // parola è legittima altrove (p.es. "Catalogo" nella tendina ma non
  // come voce di menu principale).
  if (zona) {
    const m = h.match(new RegExp(`<${zona}[\\s>][\\s\\S]*?</${zona}>`, "i"));
    h = m ? m[0] : "";
  }
  h = h.replace(/<[^>]+>/g, " ");
  h = h
    .replace(/&#x27;|&#39;|&apos;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&nbsp;/g, " ")
    .replace(/&#x([0-9a-f]+);/gi, (_, c) => String.fromCodePoint(parseInt(c, 16)))
    .replace(/&#(\d+);/g, (_, c) => String.fromCodePoint(+c));
  return h.replace(/\s+/g, " ").trim();
}

const norm = (s) => s.toLowerCase().replace(/[’']/g, "'").replace(/\s+/g, " ").trim();

// "intero" cerca la parola per intero: senza, una sigla come PLA
// corrisponderebbe dentro "plastica" e segnalerebbe un errore inesistente.
function contiene(testo, ago, intero) {
  if (!intero) return norm(testo).includes(norm(ago));
  const esc = ago.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(^|[^\\p{L}\\p{N}])${esc}($|[^\\p{L}\\p{N}])`, "iu").test(testo);
}

const cache = {};
let ok = 0;
const problemi = [];

for (const c of lista.controlli) {
  const chiave = c.pagina + "|" + (c.zona || "");
  if (!(chiave in cache)) cache[chiave] = testoDi(c.pagina, c.zona);
  const t = cache[chiave];
  if (t === null) { problemi.push({ ...c, esito: "PAGINA NON TROVATA" }); continue; }

  if (c.atteso !== undefined) {
    if (contiene(t, c.atteso, c.intero)) ok++;
    else problemi.push({ ...c, esito: "MANCANTE" });
  } else if (c.assente !== undefined) {
    if (!contiene(t, c.assente, c.intero)) ok++;
    else problemi.push({ ...c, esito: "ANCORA PRESENTE" });
  }
}

console.log(`Fonte: ${lista.fonte}`);
console.log(`${lista.controlli.length} controlli — ${ok} a posto, ${problemi.length} da vedere\n`);

for (const p of problemi) {
  const cosa = p.atteso !== undefined ? p.atteso : p.assente;
  console.log(`  ${p.esito.padEnd(17)} ${p.pagina}  [${p.rif}]`);
  console.log(`  ${"".padEnd(17)} «${cosa.length > 85 ? cosa.slice(0, 85) + "…" : cosa}»`);
}

if (!problemi.length) console.log("  Tutte le richieste del cliente risultano applicate.");
process.exit(problemi.length ? 1 : 0);
