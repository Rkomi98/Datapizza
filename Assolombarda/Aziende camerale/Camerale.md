# Agent: Batch “numero dipendenti” da elenco aziende (senza API)

## Obiettivo
Dato un file Excel/CSV a **una colonna** con i nomi delle aziende (es. colonna "Nome azienda"), recupera in modo automatizzato il **numero di dipendenti/addetti** dalle pagine pubbliche di *ufficiocamerale.it* (o fonti camerali equivalenti quando disponibili), producendo un output cumulativo con tracciabilità e qualità controllata.

## Vincoli e principi
- Nessun accesso API; usa solo contenuti pubblici e rispetta ToS/robots.
- Architettura **Controller + Workers** con **stato persistente** e **resume**.
- **Rate limit adattivo** (≈1–2 richieste/sec a dominio) + backoff esponenziale su 429/5xx.
- **Idempotenza**: niente duplicati, checkpoint frequenti, chiave per record stabile.
- **Qualità**: per ogni risultato salva `source_url`, `extracted_at`, e un `confidence_score` (0–1).
- **Etica**: non superare protezioni, non aggirare CAPTCHA: marca `needs_manual`. Piuttosto fermati e chiedi all'utente di continuare in quel caso

## Input
- `input.xlsx` o `input.csv` contenente una sola colonna con i nomi (accetta intestazioni: "Nome", "Nome azienda", "ragione sociale").
- Parametri di run (con default):
  - `shard_size=100`, `max_workers=6`, `retries=3`, `rps_target=1.5`.

Lo `shard_size` rappresenta la dimensione del blocco di aziende che l’Agent prende in carico in un singolo lotto di lavoro.
## Normalizzazione nomi
- Uppercase/trim; rimuovi doppi spazi; normalizza forme giuridiche (S.R.L., SRL, SOCIETA' A R.L. → "SRL"; S.P.A. → "SPA"; ecc.).
- Genera varianti di query: con/ senza punteggiatura, con/ senza forma giuridica, con virgolette.
- Se disponibile, aggiungi il comune/provincia dal nome (tra parentesi) per restringere.

## Ricerca & matching
- Strategia primaria: query mirata sul motore interno/scheda pubblica di *ufficiocamerale.it*. In alternativa, usa un motore generale con `site:ufficiocamerale.it "ragione sociale"` e apri il primo risultato coerente.
- Su elenco risultati: calcola **fuzzy score** (Levenshtein/Jaro-Winkler) tra input normalizzato e denominazione trovata; seleziona il top match se `score ≥ 0.90`. Se 0.80–0.89, marca `low_confidence` e prosegui; <0.80 → `no_match`.
- Apri la scheda azienda più promettente.

## Estrazione campi
- Cerca pattern testuali/DOM relativi a: **“Addetti”, “Numero addetti”, “Dipendenti”, “Unità locali”** e, se presente, l’anno di riferimento (es. 2023/2024).
- Preferisci valori **puntuali**; se solo **range** (es. “1–5”), estrai range e calcola un valore centrale ausiliario (solo per metriche): mantieni comunque il **testo originale**.
- Estrai eventuali metadati utili: **partita IVA/codice fiscale**, **comune/provincia**, **ATECO**, **stato impresa**.
- Salva snapshot raw (HTML/JSON) minimale della sezione da cui proviene il numero.

## Persistenza & stato
- File di stato `state.jsonl` per ogni azienda: `{id, name_raw, status: pending|in_progress|done|failed|needs_manual, attempts, last_error, last_update}`.
- Checkpoint risultati ogni 20 record in `results.parquet` (append idempotente).
- Alla ripartenza, processa solo `pending` e `in_progress` scaduti.

## Gestione errori
- Classifica errori: `transient` (timeout, 5xx), `permanent` (404, pagina incompatibile), `gated` (CAPTCHA/login).
- Retry automatico fino a 3 su `transient` con backoff; `gated` → `needs_manual`.

## Output
- `artifacts/output.xlsx` e `results.parquet` con schema **dinamico**; includi almeno:
  - `input_name`, `matched_name`, `employees_value` (numero o `null`), `employees_text` (originale), `year_ref` (se trovato),
  - `confidence_score`, `status`, `notes`,
  - `source_url`, `extracted_at`, `record_id` (hash stabile di [input_name_normalized, matched_name, source_url]).
- `needs_manual.csv` con righe non risolte o a bassa confidenza.
- `run_metrics.json` con: copertura %, errori per tipo, median/95p latenza, retry medi.
- `logs/session.log` e `raw/` con i frammenti HTML salvati.

## Criteri di qualità
- **Target**: ≥95% aziende con un valore (`employees_value` o `employees_text`), di cui ≥85% con `confidence_score ≥ 0.90`.
- Coerenza: se sulla stessa scheda appaiono più valori/anni, scegli il **più recente**; conserva gli altri in colonne “_alt”.
- Campionamento: verifica manuale a campione (50 righe) confrontando valore e anno.

## Passi operativi (Controller/Workers)
1. Carica `input.xlsx/csv`, normalizza nomi, genera `queue.jsonl`.
2. Suddividi in shard da `shard_size`, avvia fino a `max_workers` con `rps_target`.
3. Per ogni azienda:
   - Cerca → seleziona match → apri scheda → estrai campi → salva risultato → aggiorna stato.
4. Adatta dinamicamente il rate limit su HTTP 429/5xx; se l’errore rate > X%, riduci concurrency e attendi 60–120s.
5. Al termine: merge risultati, export Excel, report metriche, elenco `needs_manual`.
6. Stampa un **résumé**: record totali, % copertura, % alta confidenza, top 10 errori, tempo totale.

## Done
Produci `artifacts/output.xlsx`, `needs_manual.csv`, `run_metrics.json`, `state.jsonl`, `logs/`, `raw/`. Fine.
