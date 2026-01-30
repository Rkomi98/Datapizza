Fine-tuna la tua vita amorosa con il Machine Learning 👾

Un mini-progetto ironico: prende una frase (testo + emoji) e prova a capire che “energia” ha la tua relationship.

Cosa fa
- Classifica un messaggio in etichette come: amore, flirt, tenerezza, dobbiamo_parlare, gelosia, rabbia…
- Usa un modello italiano di Sentence Transformers per calcolare la somiglianza tra messaggi ed esempi

Come funziona
- Il dataset è una lista di coppie (testo, etichetta) in `CONVERSATIONS`.
- Ogni etichetta viene rappresentata dalla media degli embedding dei suoi esempi.
- Il messaggio in input viene confrontato con queste medie e assegnato all’etichetta più simile.

Emoji
- Se hai installato `emoji`, le emoji vengono convertite in testo descrittivo prima dell’analisi.
- Se non lo installi, lo script funziona comunque (semplicemente ignora la “traduzione” delle emoji).

Modello
- `nickprock/sentence-bert-base-italian-xxl-uncased`

Avvio rapido
1) Installa le dipendenze (con uv)
   `uv sync`
2) Esegui con un messaggio singolo
   `python relationship_energy.py "mi manchi 🥺"`
3) Modalità interattiva
   `python relationship_energy.py`

Personalizza il dataset
- Apri `relationship_energy.py` e aggiungi esempi a `CONVERSATIONS`.
- Più esempi per ogni etichetta = risultati più stabili.
- Puoi creare nuove etichette senza toccare il resto del codice.

Disclaimer
È un progetto giocoso: non sostituisce una conversazione vera 🙂
