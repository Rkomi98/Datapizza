# Best Practices per lo Scraping con Infinite Scroll e Paginazione

## 1. Principi generali
- **Rispetta i ToS e robots.txt**: accedi solo a contenuti consentiti, senza aggirare protezioni o paywall.
- **Preferisci sempre i dati strutturati**: JSON, API REST, GraphQL o CSV/XLSX ufficiali sono più affidabili dell’HTML.
- **Salva i payload raw**: conserva gli oggetti JSON, le risposte HTML o i file originali per audit e verifica successiva.
- **Schema dinamico**: non fissare le colonne a priori; estrai tutto e normalizza in una fase finale.

---

## 2. Infinite Scroll
- **Cattura le richieste di rete**: spesso i dati arrivano da chiamate XHR/JSON mentre scorri.  
  - Se individui un endpoint paginato, usa direttamente quello.
- **Scrolling simulato**: se non c’è endpoint visibile:
  - esegui scroll incrementali fino in fondo,
  - attendi caricamenti (`networkidle` o `waitForResponse`),
  - confronta il numero di elementi caricati.
- **Sentinella di fine**: interrompi quando il numero di elementi rimane invariato per N cicli consecutivi.

---

## 3. Paginazione classica
- **Pattern comuni**:  
  - URL con `?page=N` o `&offset=`  
  - link “Next/Previous” nel DOM  
  - pulsanti “Load More” che richiamano endpoint.
- **Strategia**: 
  - incrementa l’indice fino a quando la pagina restituisce 0 risultati,
  - cattura e unisci i dataset pagina per pagina.
- **Fallback**: cerca eventuali sitemap XML che elencano direttamente tutte le pagine.

---

## 4. Gestione delle performance
- **Sharding**: suddividi la lista di URL/record in blocchi (`shard_size`) per avere checkpoint frequenti e ripresa in caso di errore.
- **Rate limiting adattivo**: inizia con 1–2 richieste/secondo, riduci se ricevi 429/timeout.  
- **Backoff esponenziale**: attendi 2s → 5s → 15s in caso di errori temporanei.
- **Concorrenza controllata**: usa più worker solo se il sito regge; meglio 2–4 che 20.

---

## 5. Normalizzazione e deduplica
- **Deduplica** sui campi chiave (es. nome + regione).
- **Unisci i tag** se un’entità appare più volte con metadati diversi.
- **Conserva sia il campo “pulito” che il testo originale** (es. range “1–5 addetti” + numero centrale calcolato).

---

## 6. Qualità e validazione
- **Campionamento manuale**: apri un set casuale di record e verifica che i dati corrispondano.
- **Confronto con valori attesi**: controlla il numero totale di record o la continuità dei rank.
- **Log e report**: genera file `qa_report.json` con conteggi, percentuali di nulli e errori.

---

## 7. Audit e trasparenza
- Ogni record deve avere:
  - `source_url`
  - `extracted_at` (timestamp)
  - `record_id` (hash stabile)
- Conserva i file raw per eventuali controlli o rielaborazioni.
- Documenta eventuali limiti (es. campi mancanti, pagine bloccate).

---

## 8. Checklist rapida
- [ ] Identificare se esiste un **endpoint strutturato**.  
- [ ] Definire la strategia: **API/XHR**, **scroll**, o **paginazione classica**.  
- [ ] Impostare rate limit e retry.  
- [ ] Estrarre e salvare i payload raw.  
- [ ] Deduplicare e unire i dati.  
- [ ] Validare con campionamento e controlli numerici.  
- [ ] Esportare in Excel/CSV con audit trail.

---
