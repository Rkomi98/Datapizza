# Agent: Dataset "startup → tag → regione" (UI paginata o infinite scroll)

## Obiettivo
Costruisci un dataset completo di startup con campi almeno: `name`, `tags` (lista), `region`, `source_url`. Non fissare lo schema: cattura tutti i campi disponibili e aggiungi `extracted_at` e `record_id`.

## Regole
- Rispetta ToS/robots. Non aggirare protezioni o paywall.
- Preferisci dati **JSON/API** alla UI: intercetta le richieste di rete della pagina (XHR/GraphQL/REST). Se trovi endpoint paginati, usa quelli.
- Se non esiste API: gestisci **infinite scroll** con loop di scroll + attesa rete e **sentinella** (stop quando il numero di card non cresce per N cicli). Se c’è paginazione, segui “Next”/`?page=N`.
- Usa **rate limit adattivo**: aumenta/riduci la concorrenza in base alla latenza/429.
- Salva sempre i **payload raw** (JSON o HTML della sezione) per audit.

## Workflow
1) **Discovery**
   - Apri la pagina lista e avvia la cattura rete.
   - Se vedi endpoint XHR/GraphQL: identifica parametri (page/size/filter). Se GraphQL e consentito, usa introspection per conoscere campi/typenames.
   - In parallelo, prova a individuare **Sitemap** o URL con pattern di paginazione.

2) **Estrazione**
   - **Percorso A (API/XHR)**: itera le pagine finché la risposta è vuota; salva i payload; costruisci record `name/tags/region/source_url`.
   - **Percorso B (Infinite scroll)**: esegui scroll progressivo, dopo ogni scroll attendi caricamenti; confronta il numero di elementi; quando stabile per N cicli, estrai tutte le card.
   - **Percorso C (Paginazione)**: clicca "Next" o incrementa `page=N` finché non trovi più risultati.

3) **Parsing dinamico**
   - Mappa solo alla fine su `name`, `tags[]`, `region`, mantenendo **tutti** i campi extra.
   - Pulisci `tags` (split su virgole/chips); normalizza `region` se presente; se mancante, prova a inferirla da breadcrumb/URL.

4) **Dedup & Qualità**
   - Deduplica per `(name_normalized, region)`; unisci i `tags` in un’unica lista.
   - Campiona 30 righe: apri `source_url` e verifica i valori.
   - Esporta `output.xlsx` (1 foglio) + `raw/` (payload) + `qa_report.json` (copertura, errori, esempi).

## Done
- `output.xlsx` con tutte le righe; zero duplicati chiave; audit trail disponibile.
