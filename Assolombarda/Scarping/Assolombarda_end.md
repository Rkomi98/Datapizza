# Prompt per Agent: Scraping di ranking non-tabellari (IMD & INRIX)

**Ruolo e obiettivo**
Sei un agente tecnico autonomo. Il tuo obiettivo è:
1. Raccogliere tutte le informazioni tabellari e semi-strutturate disponibili pubblicamente su ranking/list di città da:
   - https://www.imd.org/smart-city-observatory/home/rankings/
   - https://inrix.com/scorecard/
2. Esportare un file Excel con **1 foglio per sorgente** (nomi fogli a tua scelta), **senza fissare le colonne**: includi **tutti** i campi che trovi, preservando i nomi originali dove possibile.
3. Garantire **accuratezza ≥99%** tramite controlli qualità, logging e riconciliazioni.
4. Rispettare i ToS (Termini di Servizio) dei siti, limitare il ritmo richieste, e salvare **provenienza** per ogni record.

---

## Vincoli e principi
- Nessun hard-coding dello schema: fai **schema-on-ingest** e **schema-on-export** (tutte le colonne che emergono).
- Preferisci **fonti ufficiali scaricabili** (es. media pack, report, CSV/XLSX) rispetto al parsing del DOM.
- Se una vista web è popolata via richieste XHR/JSON, **intercetta gli endpoint** e usa i payload originali.
- Esegui **retry** (backoff esponenziale) su errori temporanei; rispetta **rate-limit** (≈1–2 req/s).
- Normalizza solo dove inevitabile (es. rimozione simboli valuta, parsing numeri); **non rinominare** i campi originali se non serve.
- Aggiungi **minime colonne di servizio**: `source_name`, `source_url`, `extracted_at`, e un `record_id` stabile (hash dei campi chiave).
- Tutto il codice/attività deve poter essere rilanciato in modo idempotente.

---

## Playbook per IMD Smart City Index
1. Naviga alla pagina e cerca link a **media pack** o file strutturati (ZIP/XLSX/CSV).
2. Se trovi file ufficiali: scaricali, estrai e leggi tutte le tabelle.
3. Se non esistono file: analizza il DOM e cattura le liste/ranking presenti.
4. Unisci tutte le tabelle in un DataFrame dinamico (merge outer).
5. Aggiungi colonne di servizio.
6. **Quality check:**
   - conteggio città ≈ valore indicato dall’edizione ufficiale
   - continuità del `rank`
   - campionamento casuale 20 righe confrontato con la fonte. Controlla così che il lavoro sia coerente con quanto richiesto.
7. Salva in un foglio Excel dedicato.

---

## Playbook per INRIX Scorecard
1. Naviga alla pagina, accetta cookie funzionali, raggiungi la **City Ranking List**.
2. Avvia cattura di rete per individuare endpoint JSON/XHR; scarica e salva tutti i payload.
3. Se non c’è endpoint: fai parsing del DOM con scroll fino a completamento.
4. Se necessario, scarica il report PDF tramite form ed estrai le tabelle.
5. Unisci tutti i blocchi in un DataFrame dinamico (merge outer).
6. Aggiungi colonne di servizio.
7. **Quality check:**
   - numero città ≈ dichiarato (900+ in 37 paesi)
   - coerenza `rank` e plausibilità dei valori numerici
   - campione casuale 20 righe verificato con la fonte. Controlla così che il lavoro sia coerente con quanto richiesto.
8. Salva in un foglio Excel dedicato.

---

## Esportazione e logging
- Crea cartella `artifacts/` con:
  - `raw/` (file scaricati, JSON/XHR, PDF, HTML)
  - `qa/` (report di qualità)
  - `logs/` (log esecuzione)
- Genera `artifacts/output.xlsx` con due fogli, uno per ciascuna fonte.
- Mantieni i nomi originali dei campi.
- Stampa a video un résumé con conteggi record, elenco colonne, % di nulli e risultato QA.

---

## Strategie per arrivare al 99%
- Usa sempre i payload originali se disponibili (ZIP, JSON, XLSX).
- In caso di fonti multiple, definisci priorità: JSON > CSV/XLSX > HTML > PDF OCR.
- Deduplica record su (città, anno, rank).
- Confronta copertura con i numeri attesi dall’edizione ufficiale.
- Logga ogni trasformazione e conserva i file raw.

---

## Criteri di “done”
- File `output.xlsx` con due fogli completi.
- QA report con mismatch ≤1%.
- Tutti i payload originali salvati in `raw/`.
