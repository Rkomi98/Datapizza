#!/usr/bin/env python3
"""API per inferenza delle frasi della relationship."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from sentence_transformers import SentenceTransformer, util

from relationship_energy import CONVERSATIONS, normalize_text

# Carica le variabili d'ambiente dal file .env
load_dotenv()

MODEL_NAME = "nickprock/sentence-bert-base-italian-xxl-uncased"


class PredictRequest(BaseModel):
    text: str


class Score(BaseModel):
    label: str
    score: float
    percent: float


class PredictResponse(BaseModel):
    prediction: str
    scores: List[Score]


@dataclass
class ModelState:
    model: SentenceTransformer
    label_embeddings: Dict[str, np.ndarray]


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


def softmax(scores: List[float]) -> List[float]:
    arr = np.array(scores, dtype=np.float32)
    arr -= arr.max() if arr.size else 0.0
    exp = np.exp(arr)
    return (exp / exp.sum()).tolist() if exp.sum() != 0 else [0.0 for _ in scores]


def build_state() -> ModelState:
    model = SentenceTransformer(MODEL_NAME)
    label_embeddings = build_label_embeddings(model, CONVERSATIONS)
    return ModelState(model=model, label_embeddings=label_embeddings)


state = build_state()

app = FastAPI(title="Relationship Energy API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def index() -> FileResponse:
    return FileResponse("static/index.html")


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest) -> PredictResponse:
    text = payload.text.strip()
    normalized = normalize_text(text)
    message_embedding = state.model.encode(normalized, convert_to_tensor=True)

    labels = []
    scores = []
    for label, label_embedding in state.label_embeddings.items():
        score = util.cos_sim(message_embedding, label_embedding).item()
        labels.append(label)
        scores.append(score)

    probs = softmax(scores)
    combined = [
        Score(label=label, score=score, percent=prob * 100.0)
        for label, score, prob in zip(labels, scores, probs)
    ]
    combined.sort(key=lambda item: item.score, reverse=True)

    prediction = combined[0].label if combined else ""
    return PredictResponse(prediction=prediction, scores=combined)
