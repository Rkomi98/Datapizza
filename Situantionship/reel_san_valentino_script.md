# Reel Script — San Valentino (community nerd GenAI)
## Titolo (working title)
**“Misuro l’energia dei messaggi: embeddings, cosine similarity e… gelosia 😅”**

## Formato
- Durata target: 45–60s
- Stile: face-cam + screen recording (editor/terminal) + overlay grafici “spazio vettoriale”
- Tone: nerd, ironico, ma chiaro (no “magia”, solo matematica + dataset)

---

## Struttura scena-per-scena (con voce + testo a schermo)

### 0:00–0:03 — Hook
**Video (in camera):** tu con una chat aperta (sfocata) + testo grande.

**Testo on-screen:** “Che *energia* ha questo messaggio?”

**Voiceover:**
“Ok community di nerd GenAI: per San Valentino vi faccio vedere un modellino che classifica l’energia di un messaggio.”

---

### 0:03–0:08 — Il problema (super concreto)
**Video (screen):** appare un messaggio esempio in sovrimpressione.

**Testo on-screen (messaggio):** “Mi manchi da morire 💔”

**Voiceover:**
“Tipo: questo è *amore*? *drama*? o *dobbiamo parlare*?”

---

### 0:08–0:15 — Output (le classi)
**Video (screen):** lista “energie” scorre veloce.

**Testo on-screen (lista rapida):**
`amore · tenerezza · flirt · sarcasmo · dobbiamo_parlare · gelosia · rabbia · delusione · bisogno_spazio · supporto · organizzazione · scuse`

**Voiceover:**
“Io ho definito queste classi. È un classificatore semantico: gli dai una frase e ti sputa l’etichetta con una confidenza.”

---

### 0:15–0:22 — Plot twist: non è una LLM generativa
**Video (in camera):** stacchetto “plot twist”.

**Testo on-screen:** “Non è GPT che ‘indovina’”

**Voiceover:**
“Plot twist: non è un prompt su GPT. Qui uso embeddings: trasformo testo in vettori e confronto distanze.”

---

### 0:22–0:35 — Il modello dietro (spiegazione nerd ma semplice)
**Video (screen):** apri `relationship_energy.py` e zoom su 3 cose: modello, dataset, media degli embedding.

**Testo on-screen (code highlight):**
- `MODEL_NAME = "nickprock/sentence-bert-base-italian-xxl-uncased"`
- `CONVERSATIONS = [(testo, etichetta), ...]`
- `label_embedding = mean(embeddings_della_classe)`

**Voiceover (chiaro, a frasi corte):**
“Uso un Sentence-BERT italiano: ogni frase diventa un vettore in uno spazio semantico.”
“Poi mi creo un ‘prototipo’ per ogni energia: prendo esempi etichettati, li embeddo, e faccio la media.”
“Quando arriva un nuovo messaggio, lo embeddo e calcolo la cosine similarity con ogni prototipo. Vince il più simile.”

---

### 0:35–0:41 — Bonus nerd: le emoji non sono rumore
**Video (screen):** zoom su `normalize_text()` e la riga `demojize`.

**Testo on-screen:** “Emoji → testo (più segnale)”

**Voiceover:**
“Extra nerd detail: se ho la libreria `emoji`, converto 💔 in parole tipo ‘broken heart’. Così l’embedding capisce meglio il mood.”

---

### 0:41–0:55 — Demo live (terminal)
**Video (screen recording):** terminale con 2–3 esempi veloci.

**Testo on-screen (comandi):**
`python relationship_energy.py "Mi manchi da morire 💔"`
`python relationship_energy.py "Mi devi un bacio"`
`python relationship_energy.py "Certo, rispondi quando puoi… tra una settimana"`

**Voiceover:**
“Guardate: questo va su *amore*… questo è *flirt*… e questo è *sarcasmo* con un livello di passivo-aggressivo che neanche Kubernetes in outage.”

---

### 0:55–0:60 — Chiusura + CTA (San Valentino)
**Video (in camera):** chiudi con energia.

**Testo on-screen:** “Vuoi aggiungere nuove energie?”

**Voiceover:**
“Se vuoi renderlo più smart: aggiungi esempi nel dataset e ricostruisci i prototipi. È literally ‘few-shot’… ma con vettori.”
“Se vi va, ditemi nei commenti quale energia manca: *ghosting*, *crumbing*, *‘non sono pronto’*… e la aggiungiamo.”

---

## Sottotitoli (versione pronta “a righe”)
1. “San Valentino per nerd GenAI: misuro l’energia dei messaggi.”
2. “Questo: ‘Mi manchi da morire 💔’ è amore o drama?”
3. “Ho definito classi: amore, flirt, sarcasmo, gelosia…”
4. “Plot twist: non è GPT. Sono embeddings + cosine similarity.”
5. “Creo un prototipo per ogni classe facendo la media degli embedding degli esempi.”
6. “Nuovo messaggio → embedding → confronto con i prototipi → etichetta + confidenza.”
7. “Bonus: emoji → testo (💔 diventa ‘broken heart’), più segnale.”
8. “Vuoi una nuova energia? Scrivila nei commenti.”

---

## Caption (testo post)
San Valentino edition per la community GenAI: un mini-classificatore che legge il *mood* dei messaggi usando **Sentence-BERT**, **prototipi per classe** e **cosine similarity**.

Commenta con una nuova energia da aggiungere: `ghosting`, `crumbing`, `panic-texting`, `situationship.exe`…

*Disclaimer:* è un progettino nerd/ironico, non “verità” sulle relazioni.

### Hashtag (facoltativi)
`#genai #machinelearning #nlp #embeddings #sentencetransformers #python #datascience #nerditalia #sanvalentino #reelsitalia`

### Pinned comment (facoltativo)
“Nuove classi da aggiungere al dataset? Scrivi: nome energia + 2 esempi di messaggi.”

---

## Versione ultra-breve (25–30s)
**0:00–0:03** “San Valentino per nerd GenAI: che energia ha questo messaggio?”
**0:03–0:10** “Non è GPT: sono embeddings. Frase → vettore.”
**0:10–0:18** “Per ogni classe faccio un prototipo: media degli embedding degli esempi.”
**0:18–0:25** “Nuovo messaggio → cosine similarity → etichetta + confidenza. Demo.”
**0:25–0:30** “Vuoi una nuova energia? Commenta e la aggiungiamo.”

---

## Note di regia (per farlo “Reel-friendly”)
- Mantieni i cut ogni 1–2 secondi nella parte di spiegazione (0:15–0:35).
- Overlay semplice: “Embedding space”, “Prototype vectors”, “cosine similarity”.
- Sfoca/anonimizza eventuali chat reali: usa esempi finti o quelli del dataset.

### Testo copertina (idea)
“San Valentino + Embeddings: il mood dei messaggi”
