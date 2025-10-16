
# 📘 Enterprise Voice/AI — Esercizi Hands‑On con ElevenLabs
**Audience:** executive & business‑tech (Sales, CS, Product, RevOps)  
**Obiettivo:** costruire in mezza giornata 5 prototipi realistici sfruttando le capability chiave della piattaforma (Tools/Webhooks, Events, Knowledge Base, Conversation Flow, Language/Voice, Agent Workflows, Agent Testing, Agent Analysis, Privacy).  
**Formato:** istruzioni operative passo‑passo + checklist + criteri di successo + troubleshooting.  
**Prerequisiti:** accesso alla piattaforma ElevenLabs; possibilità di esporre 1–2 endpoint HTTPS (mock o server locale tramite tunneling).

---

## Indice
1. [Setup Rapido (valido per tutti gli esercizi)](#setup-rapido)  
2. [E1 — Voice Agent Triage Supporto (KB + Ticket Auto)](#e1)  
3. [E2 — Sales Qualification (BANT‑light) con Workflow a rami + Calendar Hook](#e2)  
4. [E3 — Guardrail & Interruption Clinic (no overlap, no fuori contesto)](#e3)  
5. [E4 — Compliance & Analytics con Post‑Call Webhooks + Scorecard](#e4)  
6. [E5 — Cattura Alfanumerici & Handoff con Validazione + Contesto Persistente](#e5)  
7. [Appendici operative (payload, regex, checklist, scorecard)](#appendici)

---

## <a id="setup-rapido"></a>Setup Rapido (valido per tutti)
1) **Crea/Seleziona un Agent**  
   - Tab **Voice**: scegli una voce naturale; regola speaking rate/energy.  
   - Tab **Language**: imposta IT/EN; valuta auto‑detect se i team vogliono multilingua.  
   - Tab **LLM**: scegli modello e temperatura (consigliato *bassa* per risposte più controllate).  
   - Tab **Privacy**: abilita/disabilita logging secondo policy del workshop.

2) **Conversation Flow (turn‑taking)**  
   - Abilita barge‑in/interrupt **solo lato utente** (l’agente *non* parla sopra).  
   - Imposta **No‑speech timeout** (es. 1.8–2.2s), **End‑of‑utterance** sensibile ma non aggressivo.  
   - Definisci **Fallback flow**: ripeti, chiarisci, *poi* escalation.

3) **Knowledge Base (opzionale per E1/E4)**  
   - Carica FAQ/Policy (PDF/HTML/TXT).  
   - Abilita **citazioni** o callout “Fonte: …”.  
   - Evita over‑scope: 10–20 pagine mirate sono meglio di 150 generiche.

4) **Tools (Webhook HTTP)**  
   - Prepara endpoint mock (es. `POST /tickets`, `POST /meetings`, `POST /validate_code`).  
   - Salva **API key**/segreti in configurazione sicura; non hardcodare nel prompt.

5) **Testing & Analysis**  
   - **Agent Testing**: crea 3–5 scenari per esercizio.  
   - **Agent Analysis**: definisci *Success Evaluation* (goal achieved?) e *Data Collection* (estrazioni chiave).

---

## <a id="e1"></a>E1 — Voice Agent **Triage Supporto** (KB + Ticket Auto)
**Cosa costruisci:** un agente vocale che risponde a FAQ da **Knowledge Base** (RAG) e, se serve, **apre un ticket** via Tool/Webhook con i campi compilati.

### Architettura (alto livello)
```
Utente → ASR/TTS → Agent (Prompt + KB) → Tool: create_ticket (Webhook) → Sistema Helpdesk mock
                                         ↘ Analysis (success, estrazioni) → Log/Dashboard
```

### Step‑by‑step
1. **Prompt di sistema (bozza)**
   ```
   Sei un assistente di supporto. Rispondi in modo conciso e professionale.
   Se non trovi risposta nella Knowledge Base, non inventare: chiedi chiarimenti o proponi escalation.
   Quando l’utente segnala un problema o una richiesta non risolvibile, raccogli: nome, email, categoria, descrizione breve.
   Se hai tutti i campi, invoca il Tool create_ticket e conferma il numero di ticket all’utente.
   ```
2. **KB**
   - Carica 5–10 pagine di FAQ/Policy.  
   - Abilita “use citations” o premetti “In base alla nostra policy: …”.
3. **Tool: `create_ticket`**
   - Metodo: `POST`  
   - URL: `https://<tuo-endpoint>/tickets`  
   - **Schema (input):**
     ```json
     {
       "name": "{{vars.name}}",
       "email": "{{vars.email}}",
       "category": "{{vars.category}}",
       "summary": "{{vars.summary}}",
       "sentiment": "{{analysis.sentiment}}"
     }
     ```
   - **Mapping variabili**: usa *Data Collection* per estrarre `name`, `email`, `category`, `summary`.  
   - **Risposta attesa:** `{"ticketId":"TCK-2025-00123","status":"created"}`.
4. **Conversation Flow**
   - Se **No‑match KB**: “Posso aprire una segnalazione, ti chiedo 2 dati…”.  
   - Conferma sempre i dati **leggendoli back**.
5. **Testing (3 casi min.)**
   - *FAQ risolvibile* → nessun tool; citazione fonte.  
   - *Richiesta non in KB* → raccolta dati + tool chiamato.  
   - *Dati mancanti* → agent ripete domanda specifica (non generica).

### Deliverable & Success
- **Deliverable:** link agente, endpoint mock, log test.  
- **Criteri:**  
  - ≥90% risposte *grounded* (con fonte o “secondo policy”).  
  - Ticket creato con tutti i campi nei casi No‑match.  
  - Zero allucinazioni nei test.

### Troubleshooting
- **Risposta prolissa** → abbassa temperature; nel prompt impone “max 2 frasi”.  
- **RAG lento** → riduci KB; indicizza solo sezioni pertinenti.  
- **Campi mancanti** → aggiungi *slot‑filling* esplicito nel prompt (“chiedi esattamente X e Y”).

---

## <a id="e2"></a>E2 — **Sales Qualification (BANT‑light)** con Workflow a rami + Calendar Hook
**Cosa costruisci:** un agente che fa 3 domande BANT‑light e **ramifica** il flusso: se *qualificato*, chiama un **webhook calendario**; se *non qualificato*, invia risorsa o chiude.

### Workflow (testuale)
```
Start → Q1 (Need) → Q2 (Timing) → Q3 (Authority)
  ↘ if Qualified → Tool: create_meeting
  ↘ else → Send resource / log lead / close
```

### Step‑by‑step
1. **Workflow**
   - Nodo Q1/Q2/Q3 con condizioni (es. Need presente, Timing ≤ 3 mesi).  
   - Stato `qualified=true/false` salvato nelle variabili.
2. **Tool: `create_meeting`**
   - `POST https://<endpoint>/meetings`  
   - Body:
     ```json
     {
       "lead": {
         "name": "{{vars.name}}",
         "email": "{{vars.email}}",
         "company": "{{vars.company}}"
       },
       "slot": "{{vars.preferred_slot}}",
       "notes": "{{vars.meeting_notes}}"
     }
     ```
   - Risposta attesa: `{"calendarUrl":"https://cal.com/xyz","status":"booked"}`
3. **Prompt (estratto)**
   ```
   Obiettivo: verificare interesse reale (Need), finestra temporale (Timing ≤ 3 mesi), persona di riferimento (Authority).
   Se Qualified, proporre 2 slot e, dopo conferma, invocare create_meeting.
   Se Non Qualified, proporre risorsa (PDF/landing) e chiudere con cortesia.
   ```
4. **Testing**
   - Caso Qualified (domande coerenti; tool chiamato).  
   - Caso Not Qualified (nessun tool).  
   - Caso “Need ma Timing > 6 mesi” (invio risorsa e chiusura).

### Deliverable & Success
- **Deliverable:** workflow esportato + video demo 90s.  
- **Criteri:** tool chiamato **solo** quando `qualified=true`; i dati lead popolati; slot confermato.

### Troubleshooting
- **Calendario non risponde** → mock; esegui retry (max 1).  
- **Agente insiste sugli slot** → imposta limite “max 2 proposte poi link”.

---

## <a id="e3"></a>E3 — **Guardrail & Interruption Clinic** (no overlap, no fuori contesto)
**Cosa costruisci:** una configurazione solida di **Conversation Flow** per evitare che l’agente **parli sopra** l’utente e per tenerlo **nel contesto**.

### Parametri consigliati (punto di partenza)
- **Barge‑in (utente)**: ON  
- **Agent barge‑in**: OFF  
- **End‑of‑utterance**: Sensitivity *media*  
- **No‑speech timeout**: 2.0s  
- **Max response length**: frasi brevi (prompt)  
- **Ask‑confirm loop**: ON per campi critici (email/codici)

### Step‑by‑step
1. **Regola il turn‑taking**
   - Simula 3 casi (utente interrompe / rumore / pausa).  
   - Verifica nelle **metriche** che il tempo di inizio risposta agent > fine utterance utente.
2. **Definisci Guardrail Prompt**
   ```
   Rimani nel perimetro del supporto clienti.
   Se l’utente chiede fuori ambito, rispondi: “Non sono la persona giusta; posso aprire un ticket o passarti a un collega.”
   Mai fornire istruzioni tecniche interne o dati sensibili.
   ```
3. **Fallback gerarchico**
   - 1°: riformula domanda;  
   - 2°: chiarisci opzioni;  
   - 3°: escalation (handoff/umano).
4. **Testing**
   - “FUORI CONTESTO”: agent rifiuta con formula predefinita;  
   - “OVERLAP”: nessuna sovrapposizione in 3 tentativi;  
   - “SILENZIO”: agent chiude con saluto e canale alternativo.

### Deliverable & Success
- **Deliverable:** export Conversation Flow + report test.  
- **Criteri:** 0 overlap; nessuna risposta fuori perimetro nei test; latenza percepita <1.5s.

### Troubleshooting
- **Interruzioni non riconosciute** → aumenta sensibilità barge‑in; riduci lunghezza frasi.  
- **Agent divaga** → prompt più restrittivo + KB obbligatoria + risposta “non so” elegante.

---

## <a id="e4"></a>E4 — **Compliance & Analytics** con Post‑Call Webhooks + Scorecard
**Cosa costruisci:** pipeline post‑chiamata che invia transcript/metriche a un tuo endpoint e genera una **scorecard** (esito, sentiment, red‑flag).

### Architettura
```
Agent → Transcript + Analysis → Post-Call Webhook → Endpoint (DB) → Dashboard Scorecard
```

### Step‑by‑step
1. **Agent Analysis**
   - *Success Evaluation*: definisci criteri (es. “FAQ corretta o ticket creato”).  
   - *Data Collection*: estrai `intent`, `category`, `escalation_used`, `next_step`.
2. **Post‑Call Webhook**
   - `POST https://<endpoint>/postcall`  
   - Body (esempio):
     ```json
     {
       "callId": "{{meta.call_id}}",
       "agent": "{{meta.agent_id}}",
       "transcript": "{{analysis.transcript}}",
       "metrics": {
         "success": "{{analysis.success}}",
         "sentiment": "{{analysis.sentiment}}",
         "durationSec": "{{analysis.duration}}"
       },
       "extractions": "{{analysis.extractions}}",
       "timestamp": "{{meta.timestamp}}"
     }
     ```
3. **Dashboard**
   - Tabella con 5–10 chiamate: Success (✓/✕), Sentiment, Red‑flag (policy violata?), Next‑step.
4. **Testing**
   - 3 scenari con success=true/false e 1 violazione controllata (linguaggio inappropriato → red‑flag).

### Deliverable & Success
- **Deliverable:** repo con endpoint + screenshot dashboard.  
- **Criteri:** tutte le chiamate hanno transcript & metriche salvati; red‑flag identificata quando presente.

### Troubleshooting
- **Payload grande** → usa compressione o link a storage;  
- **Sentiment erratico** → normalizza su media mobile o classi (pos/neu/neg).

---

## <a id="e5"></a>E5 — **Cattura Alfanumerici & Handoff** con Validazione + Contesto Persistente
**Cosa costruisci:** flusso robusto per **codici fiscali / targhe / ID pratica**, con **conferma** e **validazione server‑side**, e **trasferimento** tra sistemi senza perdere il contesto.

### Best practice di dettatura
- Chiedi **spelling** lettera‑per‑lettera (“A come Ancona…” solo se l’ASR fatica).  
- **Ripeti** la stringa completa e chiedi **conferma** (Sì/No).  
- Se No → chiedi “quali caratteri correggo?”.

### Validazione (server)
- Endpoint: `POST /validate_code` → `{ "raw": "RSSMRA85M01H501Z", "type": "codice_fiscale" }`  
- Risposta:
  ```json
  { "valid": true, "normalized": "RSSMRA85M01H501Z", "errors": [] }
  ```
- **Regex utili (IT):**
  - *Codice fiscale* (base): `^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$`
  - *Targa generica (semplificata)*: `^[A-Z0-9-]{5,8}$` (adatta al demo — raffinare per formato reale)

### Handoff & contesto
- Prima del trasferimento invia a `POST /handoff` uno **snapshot di sessione**:
  ```json
  {
    "sessionId": "{{meta.session_id}}",
    "customer": { "name": "{{vars.name}}", "phone": "{{vars.phone}}" },
    "captured": { "code": "{{vars.code}}", "type": "{{vars.code_type}}" },
    "transcript_so_far": "{{analysis.transcript}}"
  }
  ```
- All’aggancio del nuovo sistema, **re‑idrata** lo stato (evita di “ricominciare da zero”).

### Step‑by‑step
1. **Workflow Capture → Confirm → Validate → (loop)**  
2. **Tool `validate_code`** per il check server‑side; logga `normalized`.  
3. **Se valido** → continua; **se non valido** → chiedi parti da correggere.  
4. **Handoff**: invia snapshot e concludi con “Ti passo al collega, hai già fornito il codice…”.

### Deliverable & Success
- **Deliverable:** workflow, endpoint di validazione, log di 10 test.  
- **Criteri:** ≥95% catture corrette su 20 input; contesto integro dopo 2 trasferimenti.

### Troubleshooting
- **Ambiguità (B/V, D/T, M/N)** → chiedi spelling NATO alternativo;  
- **Rumore** → abbassa soglia end‑of‑utterance; chiedi conferma lenta.

---

## <a id="appendici"></a>Appendici operative

### A. Esempi di Endpoint (Node/Express, pseudo‑secure)
```js
import express from "express";
const app = express();
app.use(express.json());

// Ticket creation
app.post("/tickets", (req,res)=>{
  const {name,email,category,summary} = req.body;
  if(!name || !email) return res.status(400).json({error:"missing fields"});
  const ticketId = "TCK-"+Date.now();
  return res.json({ticketId, status:"created"});
});

// Meeting booking (mock)
app.post("/meetings", (req,res)=>{
  const {lead, slot} = req.body;
  if(!lead?.email || !slot) return res.status(400).json({error:"missing"});
  return res.json({calendarUrl:"https://cal.com/demo/"+Date.now(), status:"booked"});
});

// Validate codes
app.post("/validate_code", (req,res)=>{
  const {raw, type} = req.body;
  const up = (raw||"").toUpperCase().replace(/\s+/g,"");
  let valid = false;
  if(type==="codice_fiscale") valid = /^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$/.test(up);
  if(type==="targa") valid = /^[A-Z0-9-]{5,8}$/.test(up);
  res.json({valid, normalized: up, errors: valid?[]:["pattern_mismatch"]});
});

// Post-call analytics
app.post("/postcall", (req,res)=>{
  // Store transcript + metrics (use a DB in production)
  console.log("POSTCALL", req.body.callId);
  res.json({stored:true});
});

app.listen(3000, ()=>console.log("Mock endpoints on :3000"));
```

### B. Scorecard (CSV/Markdown)
| CallId | Success | Sentiment | Red‑flag | Next Step | Notes |
|---|---|---|---|---|---|
| C001 | ✓ | Pos | No | Close | KB matched |
| C002 | ✓ | Neu | No | Ticket | Data captured |
| C003 | ✕ | Neg | Yes | Escalate | Profanity detected |

### C. Checklist Rapida (per team)
- [ ] Prompt di sistema chiaro e breve  
- [ ] Voice & Language impostati  
- [ ] Conversation Flow (no overlap) testato  
- [ ] KB caricata (se serve) e citazioni attive  
- [ ] Tool/Webhook funzionante con mapping variabili  
- [ ] Test suite (3–5 casi) in Agent Testing  
- [ ] Analysis/Success configurato + Post‑Call Webhook (E4)  
- [ ] Privacy/Logging coerenti con policy

### D. Template BANT‑light (script)
```
A: Ciao, sono l’assistente. Posso farti 2–3 domande rapide per capire se ha senso fissare una call?
U: Ok.
A: Qual è la sfida principale che vuoi risolvere (es. tempi di risposta, deflection, outbound)?
A: In che finestra temporale vi muovereste per una soluzione (1–3 mesi / 3–6 / oltre)?
A: Se vedeste valore, chi dovrebbe essere coinvolto per decidere?
A: Posso proporti due slot? [oggi 16:30 / domani 11:00]
```

---

**Nota finale:** gli esercizi sono pensati per essere **indipendenti**: puoi assegnarli come track parallele ai team, oppure farli in sequenza (E3 prima di E1/E2/E5 per “mettere in sicurezza” turn‑taking e guardrail).

