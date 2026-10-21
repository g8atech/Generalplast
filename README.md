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

## Verifica visiva

`tools/compare.cjs` fotografa il sito ricostruito e quello di riferimento sulle
stesse rotte, a desktop e mobile, e `tools/diff.py` confronta le immagini pixel
per pixel. Le aree occupate da GIF animate vengono escluse: altrimenti si
misurerebbe l'animazione invece del layout.

```bash
OUT=/tmp/cmp node tools/compare.cjs && python3 tools/diff.py /tmp/cmp
```

Serve quando si rifà un sito esistente e il risultato deve coincidere, e come
rete di sicurezza prima di ogni pubblicazione.

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
