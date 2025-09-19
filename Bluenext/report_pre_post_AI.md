# Report pre/post corso AI – Analisi comparativa survey

## Procedura di analisi
- Raccolta dei due file CSV prima e dopo il corso erogato.
- Allineamento delle colonne confrontabili: normalizzazione dei nomi, rimozione dei duplicati per partecipante e armonizzazione delle scale (Likert 1–4 e frequenze 1–3) in valori numerici.
- Individuazione delle domande non sovrapponibili e creazione di due dataset “puliti” e comparabili per le variabili principali (familiarità, frequenza d’uso, atteggiamento, percezioni di impatto, valutazioni post corso).
- Calcolo delle statistiche descrittive chiave, con verifica dei min/max per ogni colonna (tabella riassunta in `scale_summary.csv` e nella dashboard Plotly).
- Analisi dei commenti aperti per estrarre temi ricorrenti pre e post corso.

## Sommario esecutivo
- La familiarità media con l’AI passa da 3.29/5 a 3.92/5 (+0.63 punti), con il valore minimo post corso che non scende mai sotto 2: la platea risulta decisamente più competente.
- L’uso quotidiano di strumenti AI cresce dal 56% al 82% dei rispondenti, mentre gli “sperimentatori occasionali” crollano dal 18% al 2%.
- Cala l’incertezza: le persone che “vogliono pensarci meglio” sull’impatto sul lavoro passano da 20% a 0%, e spariscono i “per niente d’accordo”.
- La percezione del rischio di “perdere capacità” resta articolata ma si sposta verso il “Per niente”: +5 punti, segno di maggior fiducia nel mantenere le competenze.
- Il corso è valutato positivamente (soddisfazione media 3.81/5), con picchi sulle esercitazioni pratiche (medie tra 3.1 e 3.2 su scala 1–4) e punto debole nella collaborazione fra colleghi (2.40/4).
- Temi ricorrenti nei commenti: forte domanda di automazione nello sviluppo software, necessità di use case mirati per marketing/operations, desiderio di integrazione con strumenti aziendali e supporto continuo.

## Evidenze quantitative
- **Familiarità con l’AI (scala 1–5)**: media +0.63; share dei valori 4–5 sale dal 58% al 80%. Nessuno nel post si colloca sotto il livello 2.
- **Frequenza d’uso (1=sporadico, 3=quotidiano)**: media da 2.38 a 2.80; uso quotidiano +26 punti percentuali; quasi annullata la fascia “ho provato qualche volta”.
- **Atteggiamento verso l’introduzione dell’AI**: gli entusiasti passano dal 58% al 67%; scompare il profilo “preoccupato, voglio più informazioni”.
- **Impatto percepito**:
  - Sul lavoro: “Del tutto” passa dal 47% al 67%, gli indecisi scendono a zero.
  - Sulla società: aumento del 9% di “Del tutto” e dimezzamento di “Voglio pensarci meglio”.
  - Rischio di perdita di capacità: “Per niente” sale al 29%, “Del tutto” scende al 10%, indicando una percezione del rischio più equilibrata.
- **Utilizzo strumenti specifici (scala 0–2)**: Copilot Chat (+0.65) e Copilot Office (+0.58) sono i salti maggiori; lieve arretramento per Gemini (–0.18).
- **Valutazione del corso (scala 1–4)**: Chiarezza argomenti 3.12, utilità attività pratiche 3.10, capacità di applicare quanto visto 2.94. Coinvolgimento 2.75 e collaborazione 2.40 suggeriscono margini di miglioramento. La soddisfazione complessiva è 3.81/5, con il 40% delle risposte su 4 e il 27% su 5.
- **Min/max per colonna**: il riepilogo completo con scale e range è disponibile nella dashboard e in `scale_summary.csv` (es. frequenza sempre 1–3, familiarità 1–5 pre vs 2–5 post, tutte le metriche post-course comprese fra 1 e 4).
- Grafici interattivi, tabelle di dettaglio e breakdown min/max sono pubblicati in `dashboard_feedback.html` (Plotly, apribile da browser).

## Evidenze qualitative
- **Esigenze pre corso**: richieste molto concrete su automazione dello sviluppo (refactoring, unit test, integrazione con codebase), knowledge management interno (ricerca fra documenti, casi precedenti, check-list), marketing analytics e pianificazione campagne, oltre a dubbi su prompt, privacy e performance degli strumenti.
- **Cosa ha funzionato nel corso**: grande apprezzamento per esempi e use case pratici, focus su prompt engineering contestualizzato, integrazione con stack Microsoft (Copilot, Office), sessioni tecniche su API/OpenAI agenti e follow-up più avanzati.
- **Miglioramenti richiesti**: esempi ancora più aderenti ai reparti, slot di Q&A dedicati per team, maggiore profondità tecnica “low level”, supporto continuativo (community, office hour), materiali aggiornati e percorsi differenziati per ruoli.
- **Suggerimenti extra**: proseguire con attivazioni di licenze, guidance su automazioni interne, accompagnamento nel misurare benefici reali delle soluzioni AI.

## Conclusioni
- Il corso ha consolidato competenze di base e aumentato significativamente la frequenza d’uso quotidiano degli strumenti AI, soprattutto nelle aree Copilot e prompting.
- L’atteggiamento complessivo è diventato più positivo e informato, con la quasi totale scomparsa delle posizioni contrarie e una riduzione dell’incertezza percepita sull’impatto futuro.
- Permangono esigenze di supporto su applicazioni verticali e collaborazione tra team: le metriche più basse riguardano proprio questi aspetti.
- La percezione del rischio legato alla perdita di capacità resta presente ma si riequilibra, segno che la consapevolezza sull’uso responsabile è stata affrontata ma richiede continuità.

## Raccomandazioni
1. **Moduli avanzati per team**: organizzare follow-up mirati (dev, marketing, operations) con casi d’uso dedicati e sessioni Q&A periodiche.
2. **Playbook operativo**: creare guide prompt + checklist per integrare rapidamente le best practice viste nelle attività quotidiane, inclusa la valutazione dei risultati.
3. **Comunità interna & supporto**: lanciare uno spazio di confronto continuativo (canale Teams/Office hour) per condividere esperimenti, problemi e soluzioni.
4. **Misurazione impatti**: definire metriche operative (tempo risparmiato, qualità output, riduzione errori) per monitorare benefici e indirizzare investimenti futuri.
5. **Collaborazione cross-team**: sviluppare esercitazioni congiunte e progetti pilota che favoriscano la collaborazione, per alzare il punteggio su questo indicatore.

## Output prodotti
- Dashboard interattiva: `dashboard_feedback.html`.
- Tabelle di dettaglio: `dashboard_table.csv`, `scale_summary.csv`.
- Script generatore aggiornato: `feedback_dashboard.py` (usa Plotly per grafici e tabelle).
