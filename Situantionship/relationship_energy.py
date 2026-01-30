#!/usr/bin/env python3
"""Classifica i messaggi della tua relationship in base all'energia."""

from __future__ import annotations

import argparse
from typing import Dict, List, Tuple

import numpy as np

try:
    import emoji as emoji_lib
except Exception:  # pragma: no cover - optional dependency
    emoji_lib = None

from sentence_transformers import SentenceTransformer, util

MODEL_NAME = "nickprock/sentence-bert-base-italian-xxl-uncased"

# Dataset di conversazioni (testo, etichetta).
# Aggiungi esempi per migliorare le classi.
CONVERSATIONS: List[Tuple[str, str]] = [
    ("Non riesco a smettere di pensarti.", "amore"),
    ("Mi manchi da morire 💔", "amore"),
    ("Vorrei addormentarmi con te.", "amore"),
    ("Che bello sentirti, mi mancavi ❤️", "amore"),

    ("Sei la mia persona preferita 💞", "tenerezza"),
    ("Mi fai sorridere anche quando non ci sei", "tenerezza"),
    ("Ti mando un abbraccio gigante 🤗", "tenerezza"),
    ("Sto sorridendo come un’idiota pensando a te", "tenerezza"),

    ("Mi piacerebbe vederti, vieni qui 😏", "flirt"),
    ("Quel vestito è stupendo 😍", "flirt"),
    ("Mi hai mandato il cuore a mille 😉", "flirt"),
    ("Mi devi un bacio", "flirt"),

    ("Sempre tu con i tuoi ritardi… fantastico 🙃", "sarcasmo"),
    ("Certo, rispondi quando puoi… tra una settimana", "sarcasmo"),
    ("Che bello essere ignorato 😌", "sarcasmo"),
    ("Ottima comunicazione, davvero", "sarcasmo"),

    ("Mi sento ignorata. Non rispondi mai.", "dobbiamo_parlare"),
    ("Possiamo parlare di noi? Seriamente 😶‍🌫️", "dobbiamo_parlare"),
    ("Dobbiamo chiarire una cosa.", "dobbiamo_parlare"),
    ("Non possiamo far finta di niente.", "dobbiamo_parlare"),
    ("Parliamo di ieri sera.", "dobbiamo_parlare"),

    ("Chi era quella che ti commentava la foto? 😒", "gelosia"),
    ("Con chi sei uscito ieri?", "gelosia"),
    ("Non mi piace come guardavi quella ragazza.", "gelosia"),
    ("Perché mi nascondi le storie?", "gelosia"),
    ("Vi siete baciati?", "gelosia"),
    ("Hai baciato qualcuno?", "gelosia"),
    ("Hai flirtato con lei?", "gelosia"),
    ("Mi hai detto tutta la verità su ieri?", "gelosia"),

    ("Sono furiosa, non ti voglio più sentire.", "rabbia"),
    ("Mi hai deluso tantissimo.", "rabbia"),
    ("Basta, è l’ultima volta.", "rabbia"),
    ("Non farmelo più.", "rabbia"),
    ("Non va bene così.", "rabbia"),

    ("Ma ti sembra di esserti comportato bene?", "delusione"),
    ("Non è ok quello che hai fatto.", "delusione"),
    ("Mi aspettavo altro da te.", "delusione"),
    ("Sto male per come mi hai trattato.", "delusione"),

    ("Ho bisogno di un po’ di spazio.", "bisogno_spazio"),
    ("Non scrivermi per qualche giorno.", "bisogno_spazio"),
    ("Mi serve tempo per me.", "bisogno_spazio"),
    ("Preferisco stare da sola stasera.", "bisogno_spazio"),

    ("Come stai oggi? Sono qui per te.", "supporto"),
    ("Se ti va di parlarne ti ascolto.", "supporto"),
    ("Ti sono vicino, davvero.", "supporto"),
    ("Vai bene così, non devi dimostrare nulla.", "supporto"),

    ("Ci vediamo alle 19?", "organizzazione"),
    ("Sei libero domani sera?", "organizzazione"),
    ("Appuntamento alle 8 davanti al cinema.", "organizzazione"),
    ("Ti va una pizza sabato?", "organizzazione"),
    ("Ti va di uscire insieme?", "organizzazione"),
    ("Ti va di vederci stasera?", "organizzazione"),
    ("Organizziamo qualcosa per domani?", "organizzazione"),

    ("Scusa se ho esagerato.", "scuse"),
    ("Mi dispiace per ieri.", "scuse"),
    ("Ho sbagliato, perdonami.", "scuse"),
    ("Sorry, ho reagito male.", "scuse"),
]


def normalize_text(text: str) -> str:
    cleaned = text.strip().lower()
    if emoji_lib:
        # Trasforma le emoji in testo descrittivo per dare più segnale al modello.
        cleaned = emoji_lib.demojize(cleaned, delimiters=(" ", " "))
    return " ".join(cleaned.split())


def build_label_embeddings(
    model: SentenceTransformer, dataset: List[Tuple[str, str]]
) -> Dict[str, np.ndarray]:
    label_to_texts: Dict[str, List[str]] = {}
    for text, label in dataset:
        label_to_texts.setdefault(label, []).append(text)

    label_embeddings: Dict[str, np.ndarray] = {}
    for label, texts in label_to_texts.items():
        normalized = [normalize_text(text) for text in texts]
        embeddings = model.encode(normalized, convert_to_tensor=True)
        label_embeddings[label] = embeddings.mean(dim=0)
    return label_embeddings


def classify_message(
    model: SentenceTransformer,
    label_embeddings: Dict[str, np.ndarray],
    message: str,
) -> List[Tuple[str, float]]:
    normalized = normalize_text(message)
    message_embedding = model.encode(normalized, convert_to_tensor=True)

    scores = []
    for label, label_embedding in label_embeddings.items():
        score = util.cos_sim(message_embedding, label_embedding).item()
        scores.append((label, score))

    return sorted(scores, key=lambda item: item[1], reverse=True)


def run_interactive(model: SentenceTransformer, label_embeddings: Dict[str, np.ndarray]) -> None:
    print("Scrivi un messaggio (invio per uscire):")
    while True:
        try:
            message = input("> ").strip()
        except EOFError:
            print("\nCiao!")
            break
        if not message:
            print("Ciao!")
            break
        results = classify_message(model, label_embeddings, message)
        top_label, top_score = results[0]
        print(f"Energia: {top_label} (confidenza {top_score:.3f})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classifica l'energia di un messaggio in italiano.",
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="Messaggio da analizzare. Se omesso, parte la modalità interattiva.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = SentenceTransformer(MODEL_NAME)
    label_embeddings = build_label_embeddings(model, CONVERSATIONS)

    if args.message:
        results = classify_message(model, label_embeddings, args.message)
        top_label, top_score = results[0]
        print(f"Energia: {top_label} (confidenza {top_score:.3f})")
        print("Dettaglio:")
        for label, score in results:
            print(f"- {label}: {score:.3f}")
    else:
        run_interactive(model, label_embeddings)


if __name__ == "__main__":
    main()
