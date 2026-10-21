# Strumenti di migrazione

Usati una volta sola per trasportare il sito Generalplast dalla versione
TanStack/Lovable a questo template, senza ricopiare il markup a mano.

- `extract.py` — scarica l'HTML già renderizzato delle pagine e isola header,
  footer, sezione contatti e contenuto di ogni pagina.
- `generate.py` — da quel materiale scrive i file `.astro`, sostituendo i dati
  del cliente con riferimenti a `src/config/site.json`.

Servono di nuovo solo se si rifà un altro sito esistente partendo dal suo HTML.
Vanno adattati: l'elenco delle pagine e le sostituzioni sono specifici.
