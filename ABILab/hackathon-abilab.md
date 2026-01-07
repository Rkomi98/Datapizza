# Hackathon ABI Lab / AI Hub - Documento di sintesi

## Premessa: obiettivo e vincoli
L'obiettivo dell'hackathon è arrivare a un PoC **realizzabile in 1 giorno** su problemi comuni a più banche. Questo richiede scelte "semplici": pochi asset e output chiari e riusabili.

**Messaggio chiave:** **PoC non significa prodotto finito**. Puntiamo a dimostrazioni funzionanti e spiegabili, non a integrazioni con sistemi enterprise o pareri legali.

**So what:** se non proteggiamo tempo e perimetro, rischiamo di non ottenere risultati presentabili a fine giornata.

## 1. Le challenge arrivate
Abbiamo ricevuto un insieme ampio di proposte, in ambiti diversi:

**Da MPS (molto dipendenti dai dati / computer vision):**
- Rilevamento di comportamenti sospetti su ATM
- Anti-manomissione documenti (computer vision)
- Stress test creditizio con supporto AI
- Formazione automatica (video tutorial)

**Da Credem (data governance / AI governance):**
- Code-to-Lineage Explainer
- Conversational Impact Analysis
- Automated Business Glossary Builder
- AI Governance Navigator

**So what:** molte proposte sono interessanti, ma non tutte sono compatibili con un hackathon di un giorno e con l'obiettivo di riuso multi-banca.

## 2. Il nostro outcome: 3 challenge finaliste
Alla luce dell'obiettivo e dei vincoli, il risultato è questo trio di challenge:

1. **AI Act Navigator** - pre-valutazione dei casi d'uso AI, con triage e output strutturati.
2. **FRIA/DPIA Evidence Builder** - bozze standardizzate con gap evidenti e checklist.
3. **Analisi di Bilancio AI** - KPI, trend e segnali spiegabili su bilanci standardizzati.

**Messaggio chiave:** **tre challenge complementari** che coprono governance, compliance e analisi di business, con output chiari e replicabili.

**So what:** abbiamo un insieme equilibrato e gestibile in 1 giorno, con un valore che resta anche oltre l'hackathon.

## 3. Le valutazioni fatte (open to discussion)
### 3.1 Criteri comuni di scelta
- Fattibilità in 1 giorno
- Impatto concreto per le banche
- Asset e dati preparabili in anticipo
- Risultati riusabili tra istituti

**Messaggio chiave:** **un'idea brillante ma molto dipendente dai dati non è una buona challenge se non la chiudiamo in giornata.**

### 3.2 Valutazione MPS
- Rilevamento ATM sospetti: **fattibilità bassa**, dipendenza da dataset reali e attività di etichettatura.
- Anti-manomissione documenti: **fattibilità bassa**, fortemente basata su computer vision e dataset non banale.
- Stress test creditizio: **fattibilità media**, ma richiede assunzioni forti e profili avanzati.
- Formazione automatica video: **non fattibile in 1 giorno**, pipeline troppo complessa per i tempi.

### 3.3 Valutazione Credem
- Code-to-Lineage Explainer: **fattibilità bassa**, complessità ingegneristica elevata e rischio su SQL legacy.
- Conversational Impact Analysis: **fattibilità media**, perché richiede un grafo di metadati/lineage già affidabile e una semantica condivisa. Senza questi prerequisiti il prototipo rischia di diventare una demo di chat, con poco valore operativo.
- Automated Business Glossary Builder: **fattibilità media**, perché serve un perimetro dati ben delimitato (poche tabelle, esempi chiari, glossario di partenza).
- AI Governance Navigator: **fattibilità alta**, bassa dipendenza da dati sensibili e allineato ad AI Act/FRIA/DPIA.

**Open to discussion:** quanto restringere il perimetro per le idee con fattibilità media (es. stress test e conversational)?

**So what:** la selezione finale privilegia l'affidabilità della demo e il riuso multi-banca rispetto alla sola originalità.

## 4. Le tre challenge, in breve
### 4.1 AI Act Navigator
- **Obiettivo:** valutazione preliminare e percorso compliance by design, senza pareri legali.
- **MVP 1 giorno:** percorso guidato + scheda caso d'uso + checklist gap.
- **Esclusioni:** valutazione legale completa, integrazioni enterprise.
- **Asset necessari:** regole, tassonomie campi, 10-15 casi d'uso di riferimento, template output.

**So what:** consente di standardizzare il primo passaggio della governance AI e ridurre attriti tra funzioni.

### 4.2 FRIA/DPIA Evidence Builder
- **Obiettivo:** bozze FRIA/DPIA comparabili con gap evidenti.
- **MVP 1 giorno:** form strutturato -> bozza documento + mappa dei gap + checklist azioni.
- **Rischi:** template troppo diversi tra banche, testo generato senza basi sufficienti.
- **Asset necessari:** template minimo, dizionario campi, regole gap, 2-3 esempi compilati.

**So what:** aumenta velocità e qualità delle bozze, con trasparenza su ciò che manca.

### 4.3 Analisi di Bilancio AI
- **Obiettivo:** prima lettura del bilancio con KPI e segnali spiegabili.
- **MVP 1 giorno:** KPI + semafori + commento breve sui numeri.
- **Esclusioni:** rating automatico, forecasting avanzato, normalizzazione universale.
- **Asset necessari:** dataset sintetici uniformi, dizionario mapping, KPI con soglie, casi test attesi.

**So what:** riduce il tempo sulla prima analisi e uniforma il linguaggio tra analisti.

## 5. Cosa portiamo a casa (deliverable e criteri)
**Deliverable minimi per team:**
- Demo funzionante
- Repository con codice e README
- Output demo (PDF/MD/JSON) + dataset/template usati
- Mini report con limiti e prossimi passi

**Criteri di valutazione trasversali:**
- Tracciabilità (fonti e regole)
- Qualità output
- Sicurezza e privacy by design
- Scalabilità (costi e operatività)

**So what:** la giuria valuta ciò che è replicabile e scalabile, non solo l'impatto scenico.

## 6. Pacchetto asset complessivo
- **AI Act Navigator:** regole, tassonomie campi, casi di riferimento, template output
- **FRIA/DPIA Builder:** template documento, dizionario campi, regole gap, esempi
- **Analisi Bilancio:** dataset sintetici, mapping voci, KPI + soglie, casi test

**Messaggio chiave:** **il kit iniziale serve a non perdere tempo su dati e regole durante l'hackathon.**

## 7. Prossimi passi operativi
1. Fissare le regole del gioco (ammesso/non ammesso, output standard)
2. Chiudere gli asset (responsabile per asset + date di consegna)
3. Pubblicare il kit iniziale (repository unico con `datasets/`, `templates/`, `rules/`, `examples/`)
4. Definire la valutazione finale (criteri + pesi + formato demo)

**So what:** senza asset chiusi e regole chiare, la competizione parte indebolita.

## 8. Punti aperti (open to discussion)
- Conferma finale delle 3 challenge
- Conferma asset disponibili e relativi responsabili
- Formato dati/template e politiche d'uso
- Griglia finale di valutazione e formato demo (5-7 minuti + Q&A)

**Messaggio chiave:** **decidere presto questi punti evita rilavorazioni e garantisce una gara equa.**
