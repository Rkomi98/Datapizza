# Situantionship.py
Fine-tuna la tua vita amorosa con il Machine Learning 👾
=====================================================

> Un mini-progetto ironico: prende una frase (testo + emoji) e prova a capire che “energia” ha la tua relationship.

[![Python](https://img.shields.io/badge/python-3.10%2B-2b2b2b?logo=python)](#)
[![Sentence-Transformers](https://img.shields.io/badge/sentence--transformers-italian--xxl-1f6feb)](#)
[![Status](https://img.shields.io/badge/status-playful-ff8a00)](#)

---

**Cards**

| 🚀 Quick Start | 🧠 How it works | 💬 Labels | 🧩 Emoji | 🧪 Dataset |
|---|---|---|---|---|
| `uv sync` | Embedding medi | Amore, Flirt, Gelosia… | Demojize opzionale | `CONVERSATIONS` |

---

## Cosa fa
- Classifica un messaggio in etichette come: **amore**, **flirt**, **tenerezza**, **dobbiamo_parlare**, **gelosia**, **rabbia**…
- Usa un modello italiano di Sentence Transformers per calcolare la somiglianza tra messaggi ed esempi

## Come funziona
1) Il dataset è una lista di coppie `(testo, etichetta)` in `CONVERSATIONS`.
2) Ogni etichetta viene rappresentata dalla **media degli embedding** dei suoi esempi.
3) Il messaggio in input viene confrontato con queste medie e assegnato all’etichetta più simile.

## Modello
`nickprock/sentence-bert-base-italian-xxl-uncased`

## Emoji
- Se hai installato `emoji`, le emoji vengono convertite in testo descrittivo prima dell’analisi.
- Se non lo installi, lo script funziona comunque (semplicemente ignora la “traduzione” delle emoji).

---

## Avvio rapido
```bash
uv sync
python relationship_energy.py "mi manchi 🥺"
python relationship_energy.py
```

---

## Personalizza il dataset
- Apri `relationship_energy.py` e aggiungi esempi a `CONVERSATIONS`.
- Più esempi per ogni etichetta = risultati più stabili.
- Puoi creare nuove etichette senza toccare il resto del codice.

---

## Disclaimer
È un progetto giocoso: non sostituisce una conversazione vera 🙂
