# Template siti clienti G8A

Struttura unica per i siti vetrina dei clienti. Prima istanza: **Generalplast**.

Sito statico in Astro: nessun framework a runtime, **zero JavaScript di bundle**,
HTML completo servito al primo byte. Niente dipendenze in beta, niente build che
si rompe da sola.

```
src/
  config/site.json      ← dati del cliente        } le uniche due cose
  styles/tokens.css     ← identità visiva          } da cambiare per cliente
  styles/global.css     ← tema condiviso
  components/           ← header, footer, sezione contatti
  layouts/Base.astro    ← head, meta, dati strutturati
  pages/                ← una pagina per file
public/                 ← immagini
tools/                  ← verifica visiva e funzionale
```

## Partire da qui per un nuovo cliente

1. Duplica il repository.
2. Riscrivi `src/config/site.json` — nome, contatti, P.IVA, chiave Web3Forms, dominio.
3. Riscrivi `src/styles/tokens.css` — colori, raggio, sfumature, ombre.
   Il resto del tema si adatta da solo: non si tocca né CSS né componenti.
4. Sostituisci le immagini in `public/`.
5. Scrivi le pagine in `src/pages/`.

I dati strutturati (`LocalBusiness`), la `sitemap.xml`, il `robots.txt`, i meta
per pagina e il link canonico si generano dalla configurazione: non vanno
mantenuti a mano.

## Comandi

```bash
npm install
npm run dev                  # sviluppo su localhost:4321
npm run build                # genera dist/
node tools/check-interactions.cjs   # form, menu, navigazione
```

## Immagini

Gli originali stanno in `sorgenti/`, **fuori dalla cartella pubblicata**. In
`public/` finiscono solo le versioni generate: ridimensionate alla misura in
cui vengono davvero mostrate e convertite in WebP.

```bash
python3 tools/ottimizza-immagini.py          # genera quelle mancanti
python3 tools/ottimizza-immagini.py --tutte  # rigenera tutto
```

La larghezza di destinazione è il doppio di quella di visualizzazione: su
schermi ad alta densità non si vede differenza, e si evita di servire un file
da 2048 px dentro un riquadro da 560. Le gif animate diventano WebP animato,
a parità di fotogrammi e velocità.

Tre cose imparate facendolo:

- **Dichiarare sempre `width` e `height`** sulle immagini a caricamento
  differito. Senza, finché il file non arriva l'elemento occupa altezza zero e
  al caricamento il contenuto sottostante salta.
- **Precaricare solo l'immagine che determina il primo rendering.** Il
  precaricamento è una richiesta di massima priorità: dichiararne sei
  significa bloccare la pagina su tutte e sei prima di mostrare qualcosa.
- **Il percorso del logo sta in `site.json`**, non nel markup: va aggiornato
  anche lì quando cambia l'estensione, o il logo a piè di pagina si rompe in
  silenzio.

Alzare la qualità oltre un certo punto non avvicina il risultato all'originale:
la differenza residua che si misura confrontando le schermate viene dal
ridimensionamento, non dalla compressione, ed è invisibile a grandezza reale.

## Icone del sito

```bash
python3 tools/genera-favicon.py sorgenti/logo.png --colore "#c72026"
```

Il logo di un'azienda è quasi sempre orizzontale e a 16 px diventa
illeggibile. Lo strumento isola il solo marchio — scarta scritte, ® e
frammenti tenendo la forma principale — e lo monta in bianco su un quadrato
del colore aziendale, che in una barra di schede si distingue molto meglio di
una forma sottile su fondo trasparente. Produce `favicon.ico` (16/32/48, ogni
misura disegnata alla sua risoluzione), `icon-192`, `icon-512` e
`apple-touch-icon`.

Se il ritaglio automatico prende anche parte della scritta, si limita l'area
con `--ritaglio x1,y1,x2,y2`.

## Anteprima per le condivisioni

```bash
python3 tools/genera-og.py --sfondo sorgenti/hero.png --logo sorgenti/logo.png \
  --testo "Stampaggio e lavorazione materie plastiche dal 1968"
```

Produce `public/og.jpg` (1200×630): è l'immagine che compare quando il link
viene incollato in WhatsApp, LinkedIn o in una mail. Senza, il link appare
nudo. Va rigenerata se cambiano logo o claim.

## Intestazioni di sicurezza

Stanno in `vercel.json` e valgono per tutto il sito: `Content-Security-Policy`,
`X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`,
`Permissions-Policy`.

**La politica di sicurezza va collaudata prima di pubblicarla.** Se è troppo
stretta blocca la chiamata del form, e il sito sembra funzionare mentre le
richieste non partono: in produzione te ne accorgi dai lead che non arrivano.

```bash
npm run build && node tools/prova-csp.cjs
```

Serve il sito costruito applicando davvero le intestazioni di `vercel.json`,
carica ogni pagina, invia il form e segnala qualsiasi cosa venga bloccata.
Da rieseguire ogni volta che si tocca la politica o si aggiunge un servizio
esterno.

## Contrasto del testo

```bash
npm run build && node tools/contrasto.cjs
SITO=https://generalplast.it node tools/contrasto.cjs
```

Misura il contrasto fra testo e sfondo sulle combinazioni reali e segnala
quelle sotto la soglia di leggibilità (4,5:1 per il testo normale, 3:1 per
quello grande).

Due cose che rendono il risultato attendibile e che altrimenti producono
numeri falsi:

- i colori sono dichiarati in `oklch`, e il browser li restituisce in quel
  formato: leggerli come se fossero `rgb` dà valori senza senso. Lo strumento
  li fa convertire al browser stesso, dipingendoli su una tela e rileggendone
  i byte;
- il testo sopra una fotografia viene escluso, perché lì il contrasto dipende
  dall'immagine e va giudicato a occhio, non calcolato.

Il tema ha `--primary-su-scuro`: il rosso di marchio su fondo scuro si ferma a
2,97:1, insufficiente per un testo da 12 px, quindi nelle sezioni scure le
etichette usano la stessa tinta più chiara.

## Pagina di errore

`src/pages/404.astro` genera la pagina mostrata quando un indirizzo non
esiste. Senza, Vercel ne serve una in inglese, senza grafica e senza modo di
tornare al sito.

## Collaudo prima della consegna

```bash
SITO=https://generalplast.it node tools/collaudo.cjs
```

Controlla sul sito pubblicato: lunghezza di titoli e descrizioni, indirizzo
canonico, lingua, un solo H1, gerarchia dei titoli senza salti, testi
alternativi, campi del modulo con etichetta associata, dati strutturati,
link interni ed esterni raggiungibili, risorse mancanti, errori in console,
titoli e descrizioni non duplicati fra pagine.

Nota: `garanteprivacy.it` risponde 403 alle richieste automatiche. È un falso
positivo, il link funziona da browser.

## Le tre verifiche

Sono indipendenti e servono a cose diverse. Prima di ogni pubblicazione
importante vanno eseguite tutte e tre.

| | Risponde a | Quando serve |
|---|---|---|
| `verifica-richieste.cjs` | Le modifiche chieste dal cliente sono state recepite? | Sempre |
| `check-interactions.cjs` | Form, menu e navigazione funzionano? | Sempre |
| `compare.cjs` + `diff.py` | La resa coincide con un riferimento? | Quando si rifà un sito esistente |

Le prime due bastano a sé stesse. La terza richiede un sito di riferimento
con cui confrontarsi e serve soprattutto durante una migrazione.

Nota: **nessuna delle prime due sa cosa il cliente aveva chiesto**, e il
confronto visivo nemmeno. Se una richiesta non fosse stata recepita nel sito
di partenza, verrebbe copiata fedelmente sbagliata e tutti i controlli
passerebbero lo stesso. È per questo che `richieste-cliente.json` esiste: si
scrive a mano dal documento del cliente, ed è l'unico controllo che guarda
all'origine invece che alla copia.

## Verifica delle richieste del cliente

`tools/richieste-cliente.json` elenca, pagina per pagina, i testi che devono
comparire (`atteso`) e quelli che devono essere spariti (`assente`).
`tools/verifica-richieste.cjs` li controlla sul sito costruito.

```bash
npm run build && node tools/verifica-richieste.cjs
```

Due accortezze imparate sul campo:

- `"intero": true` cerca la parola per intero. Senza, la sigla `PLA`
  corrisponde dentro «**pla**stica» e segnala un errore inesistente.
- `"zona": "nav"` limita il controllo a header, main o footer. Serve quando
  una parola è legittima altrove — «Catalogo» non deve più essere una voce di
  menu, ma resta giusta dentro il link alla tendina.

Per un nuovo cliente la lista si riscrive dal suo elenco di modifiche. È
mezz'ora di lavoro e da lì in poi ogni pubblicazione si ricontrolla da sola.

## Verifica visiva

`tools/compare.cjs` fotografa il sito ricostruito e quello di riferimento sulle
stesse rotte, a desktop e mobile, e `tools/diff.py` confronta le immagini pixel
per pixel. Le aree occupate da GIF animate vengono escluse: altrimenti si
misurerebbe l'animazione invece del layout.

```bash
LIVE=https://sito-di-riferimento OUT=/tmp/cmp node tools/compare.cjs
python3 tools/diff.py /tmp/cmp
```

Con `NEW` confronta un indirizzo pubblicato invece della build locale: serve a
verificare la produzione, dove emergono cose che in locale non si vedono.

`tools/diff-testi.cjs` affianca invece il **testo visibile** di due indirizzi,
parola per parola. Il confronto a schermate non intercetta una modifica fatta
sul sito di riferimento dopo la copia, perché confronta sempre contro la
versione corrente di quel sito.

```bash
REF=https://riferimento MINE=https://nostro node tools/diff-testi.cjs
```

Nessuno dei due ha un indirizzo predefinito: il sito di riferimento di una
migrazione va spento una volta finita, e uno strumento che ci punta da solo
smetterebbe di funzionare senza dirlo.

## Form contatti

Va a Web3Forms, chiave in `src/config/site.json` → `form.accessKey`. La chiave non è un
segreto: funziona come alias dell'indirizzo di destinazione e può stare nel
codice pubblico.

La conferma compare **solo** se il servizio risponde `success: true`; in ogni
altro caso compare un errore con il numero di telefono. Un form che finge di
aver spedito è peggio di un form assente: il cliente perde richieste senza
accorgersene.

Il consenso privacy è obbligatorio e il campo `botcheck` è una trappola
anti-spam.

## Statistiche, Search Console e cookie

Scelta di base del template: **statistiche senza cookie** (Vercel Web Analytics,
servito dal dominio stesso). Niente consenso da raccogliere, niente banner,
niente cookie policy — e i dati si raccolgono dal 100% dei visitatori invece
che dalla sola quota che accetta.

**Search Console** non richiede codice: si verifica con un record TXT sul DNS.
Solo se il DNS non è raggiungibile si usa `verification.google` in
`src/config/site.json`, che emette il meta tag.

**Google Analytics e Microsoft Clarity non vanno aggiunti così come sono.**
Scrivono cookie e sono strumenti di tracciamento: le linee guida del Garante
impongono il blocco preventivo degli script e la raccolta del consenso prima
che partano. Aggiungerli significa mettere in conto anche:

- un banner con rifiuto allo stesso livello dell'accettazione e nessuna casella
  pre-spuntata;
- gli script caricati **solo dopo** il consenso, mai prima;
- una cookie policy e l'aggiornamento dell'informativa;
- per Clarity, la verifica del mascheramento dei campi del modulo, che registra
  le sessioni.

Vanno riservati ai siti dove servono davvero — tipicamente quelli che fanno
campagne a pagamento e hanno bisogno di importare le conversioni. Quando
serviranno, il banner va costruito dentro questo template una volta sola, non
comprato per dominio.

## Pubblicazione su Vercel

Importa il repository: Astro viene riconosciuto da solo (`npm run build`,
output `dist`). `vercel.json` porta già:

- `X-Robots-Tag: noindex` sugli indirizzi `*.vercel.app`, così l'anteprima non
  finisce su Google a fare concorrenza al dominio vero;
- il reindirizzamento permanente `/homepage` → `/`.

Il dominio si collega da Settings → Domains.

## Anteprime per le modifiche del cliente

Vercel crea un'anteprima per ogni ramo git. Una modifica proposta su un ramo
genera il suo indirizzo di anteprima; approvata, si unisce al ramo principale e
va in produzione. È la base su cui innestare il bot per le richieste dei
clienti, senza costruire nulla di nuovo.

## Da sapere

- Le immagini pesano: vedere `tools/` per la verifica, ma la conversione in
  WebP va fatta e ricontrollata con il confronto visivo.
- `src/pages/privacy.astro` contiene un testo provvisorio. Va sostituito con
  l'informativa del cliente, che deve citare Web3Forms come responsabile
  esterno del trattamento.
