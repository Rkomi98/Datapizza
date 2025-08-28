#!/usr/bin/env python3
"""
Voicebot con FunctionalPipeline (datapizzai):
Audio → Gemini 2.5 Flash (trascrizione+riassunto+sentiment) → branch notifica → report

Requisiti:
- .env con GOOGLE_API_KEY
- pip install sounddevice soundfile python-dotenv pyyaml
- libreria datapizzai disponibile nell'ambiente

Uso tipico:
  python Pipeline/voicebot_with_datapizzai.py --config Pipeline/voicebot_pipeline.yaml

Note:
- Questo script costruisce una FunctionalPipeline con branch e foreach.
- Parametri (durata/sr/out) possono essere passati via CLI o YAML.
"""

import argparse
import importlib
import os
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

# datapizzai pipeline
from datapizzai.pipeline import Dependency, FunctionalPipeline

# componenti locali
from Pipeline.components import (
    RecordAudio,
    GeminiAudioAnalyzer,
    ExtractKey,
    BulletPointNormalizer,
    BuildReport,
    SendNotification,
)


# -----------------------------
# Configurazione & utilità base
# -----------------------------

load_dotenv()  # carica .env dal cwd
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def _load_yaml_config(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_pipeline(seconds: int, sample_rate: int, audio_path: str, out_path: str, model: str = "gemini-2.5-flash") -> FunctionalPipeline:
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY mancante. Definirlo in .env o nell'ambiente.")

    # Sottopipeline: notifica
    notify = FunctionalPipeline().run(name="send_notification", node=SendNotification())

    # Sottopipeline: normalizzazione bullet + report
    normalize_and_report = (
        FunctionalPipeline()
        .foreach(
            name="normalize_bullets",
            dependencies=[Dependency(node_name="bullets")],
            do=BulletPointNormalizer(),
        )
        .then(
            name="report",
            node=BuildReport(),
            dependencies=[Dependency(node_name="analyze")],
            kwargs={"out_path": out_path},
        )
    )

    pipeline = (
        FunctionalPipeline()
        .run(
            name="record",
            node=RecordAudio(),
            kwargs={"path": audio_path, "seconds": seconds, "sample_rate": sample_rate},
        )
        .then(
            name="analyze",
            node=GeminiAudioAnalyzer(api_key=GOOGLE_API_KEY, model=model),
            dependencies=[Dependency(node_name="record")],
            target_key="audio_path",
        )
        .then(
            name="bullets",
            node=ExtractKey(key="bullets"),
            dependencies=[Dependency(node_name="analyze")],
        )
        .branch(
            condition=lambda ctx: (ctx.get("analyze") or {}).get("sentiment") == "angry",
            dependencies=[Dependency(node_name="analyze")],
            if_true=notify,
            if_false=normalize_and_report,
        )
    )

    return pipeline


def main():
    parser = argparse.ArgumentParser(description="Voicebot con FunctionalPipeline (Gemini 2.5 Flash)")
    parser.add_argument("--config", type=str, default="Pipeline/voicebot_pipeline.yaml", help="YAML di configurazione")
    parser.add_argument("--sec", type=int, default=None, help="Durata registrazione (override YAML)")
    parser.add_argument("--sr", type=int, default=None, help="Sample rate (override YAML)")
    parser.add_argument("--audio", type=str, default=None, help="Percorso WAV (override YAML)")
    parser.add_argument("--out", type=str, default=None, help="Percorso report MD (override YAML)")
    parser.add_argument("--model", type=str, default=None, help="Modello Gemini (override YAML)")
    args = parser.parse_args()

    cfg = _load_yaml_config(args.config)

    # Parametri con fallback tra CLI -> YAML -> default
    seconds = args.sec or cfg.get("params", {}).get("seconds", 20)
    sample_rate = args.sr or cfg.get("params", {}).get("sample_rate", 16000)
    audio_path = args.audio or cfg.get("params", {}).get("audio_path", "session.wav")
    out_path = args.out or cfg.get("params", {}).get("out_path", "Pipeline/voicebot_report.md")
    model = args.model or cfg.get("params", {}).get("model", "gemini-2.5-flash")

    pipeline = build_pipeline(seconds, sample_rate, audio_path, out_path, model=model)
    results = pipeline.execute()
    print("Pipeline results keys:", list(results.keys()))



if __name__ == "__main__":
    main()
