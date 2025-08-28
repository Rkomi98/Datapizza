#!/usr/bin/env python3
"""
Voicebot con FunctionalPipeline completo (datapizzai):
Audio → Gemini 2.5 Flash (trascrizione+riassunto+sentiment) → branch notifica → report

Questo esempio dimostra l'uso completo di FunctionalPipeline con:
- run: esecuzione di nodi singoli
- then: concatenazione di nodi 
- foreach: iterazione su collezioni
- branch: condizioni per flussi alternativi
- execute: esecuzione della pipeline

Requisiti:
- .env con GOOGLE_API_KEY
- pip install sounddevice soundfile python-dotenv pyyaml
- libreria datapizzai disponibile nell'ambiente

Uso tipico:
  python Pipeline/voicebot_functional_complete.py --config Pipeline/voicebot_functional_pipeline.yaml
"""

import argparse
import os
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

# datapizzai pipeline
from datapizzai.pipeline import Dependency, FunctionalPipeline
from datapizzai.core.models import PipelineComponent

# componenti locali aggiornati  
from components import (
    RecordAudio,
    GeminiAudioAnalyzer,
    ExtractKey,
    BulletPointNormalizer,
    BuildReport,
    SendNotification,
    SentimentChecker,
)


# -----------------------------
# Configurazione & utilità
# -----------------------------

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def load_yaml_config(path: Optional[str]) -> Dict[str, Any]:
    """Carica configurazione YAML."""
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# -----------------------------
# Pipeline building con esempi 
# -----------------------------

def build_pipeline_programmatic(seconds: int, sample_rate: int, audio_path: str, 
                               out_path: str, model: str = "gemini-2.5-flash", skip_recording: bool = False) -> FunctionalPipeline:
    """
    Costruisce la pipeline programmaticamente seguendo gli esempi forniti dall'utente.
    
    Questa versione dimostra:
    - Uso di run() per nodi iniziali
    - Uso di then() per concatenazione
    - Uso di foreach() per iterare sui bullet points
    - Uso di branch() per gestire sentiment arrabbiato
    - Uso di execute() per eseguire tutto
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY mancante. Definirlo in .env o nell'ambiente.")

    # === Componenti da usare nella pipeline ===
    recorder = RecordAudio()
    analyzer = GeminiAudioAnalyzer(api_key=GOOGLE_API_KEY, model=model)
    bullet_extractor = ExtractKey(key="bullets")
    bullet_normalizer = BulletPointNormalizer()
    report_builder = BuildReport()
    notification_sender = SendNotification()

    # === Sottopipeline per notifica (se arrabbiato) ===
    notification_pipeline = (
        FunctionalPipeline()
        .run(
            name="send_notification",
            node=notification_sender,
            dependencies=[Dependency(node_name="analyze_audio")],
            kwargs={"sentiment": "angry"}
        )
    )

    # === Sottopipeline per report normale (foreach + report) ===
    normal_flow_pipeline = (
        FunctionalPipeline()
        .foreach(
            name="normalize_bullets",
            dependencies=[Dependency(node_name="extract_bullets")],
            do=bullet_normalizer,
        )
        .then(
            name="generate_report",
            node=report_builder,
            target_key="normalized_bullets",
            dependencies=[
                Dependency(node_name="analyze_audio", target_key="analysis")
            ],
            kwargs={"out_path": out_path}
        )
    )

    # === Pipeline principale ===
    if skip_recording or os.path.exists(audio_path):
        # Usa audio esistente
        print(f"📁 Usando audio esistente: {audio_path}")
        pipeline = (
            FunctionalPipeline()
            # Step 1: Analizza direttamente (salta registrazione)
            .run(
                name="analyze_audio",
                node=analyzer,
                kwargs={"audio_path": audio_path}
            )
        )
    else:
        # Registra nuovo audio
        print(f"🎙️ Registrando nuovo audio: {audio_path}")
        pipeline = (
            FunctionalPipeline()
            # Step 1: Registra audio
            .run(
                name="record_audio",
                node=recorder,
                kwargs={"path": audio_path, "seconds": seconds, "sample_rate": sample_rate},
            )
            # Step 2: Analizza con Gemini
            .then(
                name="analyze_audio",
                node=analyzer,
                target_key="audio_path",
            )
        )
    # Continua la pipeline con estrazione bullets
    pipeline = (
        pipeline
        # Step 3: Estrai bullets
        .then(
            name="extract_bullets",
            node=bullet_extractor,
            target_key="analyze_audio",
        )
        # Step 4: Branch basato su sentiment
        .branch(
            condition=lambda ctx: (ctx.get("analyze_audio") or {}).get("sentiment", "").lower() in ["angry", "very_angry", "furious"],
            dependencies=[Dependency(node_name="analyze_audio")],
            if_true=notification_pipeline,
            if_false=normal_flow_pipeline,
        )
        # Step 5: Ottieni il risultato dell'analisi
        .get("analyze_audio")
    )

    return pipeline


def build_pipeline_from_yaml(yaml_path: str, **override_params) -> FunctionalPipeline:
    """
    Costruisce la pipeline da file YAML (implementazione semplificata).
    
    Nota: datapizzai supporta FunctionalPipeline.from_yaml() ma per questo esempio
    implementiamo una versione semplificata che usa la struttura YAML proposta.
    """
    config = load_yaml_config(yaml_path)
    if not config:
        raise ValueError(f"Impossibile caricare configurazione da {yaml_path}")
    
    # Parametri con override
    params = config.get("params", {})
    params.update(override_params)
    
    return build_pipeline_programmatic(
        seconds=params.get("seconds", 20),
        sample_rate=params.get("sample_rate", 16000),
        audio_path=params.get("audio_path", "session.wav"),
        out_path=params.get("out_path", "Pipeline/voicebot_report.md"),
        model=params.get("model", "gemini-2.5-flash")
    )


# -----------------------------
# Pipeline alternativa con più esempi
# -----------------------------

class AdvancedVoicebotPipeline:
    """
    Esempio più avanzato che dimostra ulteriori pattern con FunctionalPipeline.
    
    Questo include:
    - Gestione di multipli branch
    - Uso di componenti come moduli
    - Pattern più complessi con foreach
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def build_advanced_pipeline(self, **params) -> FunctionalPipeline:
        """Costruisce una pipeline avanzata con pattern complessi."""
        
        # Componenti
        recorder = RecordAudio()
        analyzer = GeminiAudioAnalyzer(api_key=self.api_key, model=params.get("model", "gemini-2.5-flash"))
        sentiment_checker = SentimentChecker()
        
        # Sottopipeline per diversi tipi di sentiment
        angry_pipeline = FunctionalPipeline().run(
            name="handle_angry", 
            node=SendNotification(),
            kwargs={"sentiment": "angry"}
        )
        
        positive_pipeline = FunctionalPipeline().run(
            name="handle_positive",
            node=BuildReport(),
            kwargs={"out_path": params.get("out_path", "positive_report.md")}
        )
        
        neutral_pipeline = FunctionalPipeline().run(
            name="handle_neutral",
            node=BuildReport(), 
            kwargs={"out_path": params.get("out_path", "neutral_report.md")}
        )
        
        # Pipeline principale
        pipeline = (
            FunctionalPipeline()
            .run(
                name="record",
                node=recorder,
                kwargs={
                    "path": params.get("audio_path", "session.wav"),
                    "seconds": params.get("seconds", 20),
                    "sample_rate": params.get("sample_rate", 16000)
                }
            )
            .then(name="analyze", node=analyzer, target_key="audio_path")
            .branch(
                condition=lambda ctx: ctx.get("analyze", {}).get("sentiment", "").lower() == "angry",
                dependencies=[Dependency(node_name="analyze")],
                if_true=angry_pipeline,
                if_false=FunctionalPipeline().branch(
                    condition=lambda ctx: ctx.get("analyze", {}).get("sentiment", "").lower() in ["happy", "positive"],
                    dependencies=[Dependency(node_name="analyze")], 
                    if_true=positive_pipeline,
                    if_false=neutral_pipeline
                )
            )
        )
        
        return pipeline


# -----------------------------
# Main entry point
# -----------------------------

def main():
    parser = argparse.ArgumentParser(description="Voicebot con FunctionalPipeline completo")
    parser.add_argument("--config", type=str, default="Pipeline/voicebot_functional_pipeline.yaml", 
                       help="File YAML di configurazione")
    parser.add_argument("--mode", choices=["basic", "yaml", "advanced"], default="basic",
                       help="Modalità pipeline: basic (programmatic), yaml (da file), advanced (pattern complessi)")
    parser.add_argument("--sec", type=int, help="Durata registrazione (override)")
    parser.add_argument("--sr", type=int, help="Sample rate (override)")
    parser.add_argument("--audio", type=str, help="Percorso audio (override)")
    parser.add_argument("--out", type=str, help="Percorso report (override)")
    parser.add_argument("--model", type=str, help="Modello Gemini (override)")
    parser.add_argument("--skip-recording", action="store_true", help="Salta registrazione e usa audio esistente")
    args = parser.parse_args()

    try:
        # Parametri override da CLI
        overrides = {}
        if args.sec: overrides["seconds"] = args.sec
        if args.sr: overrides["sample_rate"] = args.sr  
        if args.audio: overrides["audio_path"] = args.audio
        if args.out: overrides["out_path"] = args.out
        if args.model: overrides["model"] = args.model

        # Costruisce pipeline in base alla modalità
        if args.mode == "basic":
            print("🚀 Modalità: Pipeline programmatica di base")
            config = load_yaml_config(args.config)
            params = {**config.get("params", {}), **overrides}
            params["skip_recording"] = args.skip_recording
            pipeline = build_pipeline_programmatic(**params)
            
        elif args.mode == "yaml":
            print("🚀 Modalità: Pipeline da YAML")
            overrides["skip_recording"] = args.skip_recording
            pipeline = build_pipeline_from_yaml(args.config, **overrides)
            
        elif args.mode == "advanced":
            print("🚀 Modalità: Pipeline avanzata")
            if not GOOGLE_API_KEY:
                raise RuntimeError("GOOGLE_API_KEY richiesta per modalità avanzata")
            config = load_yaml_config(args.config)
            params = {**config.get("params", {}), **overrides}
            params["skip_recording"] = args.skip_recording
            advanced_builder = AdvancedVoicebotPipeline(GOOGLE_API_KEY)
            pipeline = advanced_builder.build_advanced_pipeline(**params)

        # Esegue la pipeline
        print("🎯 Esecuzione pipeline...")
        results = pipeline.execute()
        
        # Stampa risultati
        print("✅ Pipeline completata!")
        print("📊 Risultati disponibili:")
        for key in results.keys():
            if isinstance(results[key], dict):
                print(f"  - {key}: {type(results[key]).__name__} con {len(results[key])} chiavi")
            else:
                print(f"  - {key}: {type(results[key]).__name__}")
        
        # Mostra analisi se disponibile
        if "analyze_audio" in results or "analyze" in results:
            analysis = results.get("analyze_audio") or results.get("analyze")
            if isinstance(analysis, dict):
                print(f"\n📝 Sentiment rilevato: {analysis.get('sentiment', 'N/A')}")
                transcript = analysis.get('transcript', '')
                if transcript:
                    preview = transcript[:100] + "..." if len(transcript) > 100 else transcript
                    print(f"🎙️ Trascrizione (anteprima): {preview}")
                    
    except Exception as e:
        print(f"❌ Errore durante l'esecuzione: {e}")
        raise


if __name__ == "__main__":
    main()
