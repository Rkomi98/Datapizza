#!/usr/bin/env python3
"""
Esempio di utilizzo di DagPipeline per creare un grafo di dipendenze
per l'analisi di sentimenti e generazione di report.

Requisiti:
- pip install python-dotenv
- .env con OPENAI_API_KEY o GOOGLE_API_KEY
"""

import os
from dataclasses import dataclass
from typing import Any, Dict

from dotenv import load_dotenv
from datapizzai.pipeline import DagPipeline
from datapizzai.core.models import PipelineComponent
from datapizzai.clients import OpenAIClient

# Carica variabili d'ambiente
load_dotenv()

# Componenti personalizzati - implementazione completa come nel README
class DataLoader(PipelineComponent):
    """Carica dati di esempio."""
    
    def run(self, **kwargs) -> Dict[str, Any]:
        reviews = ["Prodotto eccellente!", "Non mi piace", "Nella media"]
        return {"reviews": reviews}

class SentimentAnalyzer(PipelineComponent):
    """Analizza il sentiment dei testi."""
    
    def __init__(self, client: OpenAIClient):
        self.client = client
    
    def run(self, reviews: list, **kwargs) -> Dict[str, Any]:
        analyzed = []
        for review in reviews:
            # Simulazione analisi sentiment semplificata per l'esempio
            if "eccellente" in review:
                sentiment = "positive"
            elif "non" in review.lower():
                sentiment = "negative"
            else:
                sentiment = "neutral"
                
            analyzed.append({"text": review, "sentiment": sentiment})
        
        return {"sentiment_results": analyzed}

class StatisticsCalculator(PipelineComponent):
    """Calcola statistiche sui sentiment."""
    
    def run(self, sentiment_results: list, **kwargs) -> Dict[str, Any]:
        sentiments = [r["sentiment"] for r in sentiment_results]
        stats = {
            "positive": sentiments.count("positive"),
            "negative": sentiments.count("negative"), 
            "neutral": sentiments.count("neutral")
        }
        return {"statistics": stats}

class MetadataExtractor(PipelineComponent):
    """Estrae metadata dai reviews."""
    
    def run(self, reviews: list, **kwargs) -> Dict[str, Any]:
        metadata = {
            "total_reviews": len(reviews),
            "avg_length": sum(len(r) for r in reviews) / len(reviews),
            "timestamp": "2024-01-01"
        }
        return {"metadata": metadata}

class ReportGenerator(PipelineComponent):
    """Genera report finale combinando tutti i dati."""
    
    def run(self, sentiment_results: list, statistics: dict, metadata: dict, **kwargs) -> Dict[str, Any]:
        report = f"""
REPORT ANALISI - {metadata['timestamp']}
Recensioni totali: {metadata['total_reviews']}
Lunghezza media: {metadata['avg_length']:.1f}

SENTIMENT:
- Positive: {statistics['positive']}
- Negative: {statistics['negative']}
- Neutral: {statistics['neutral']}

DETTAGLI:
{chr(10).join(f"- {r['text']}: {r['sentiment']}" for r in sentiment_results)}
        """
        return {"final_report": report.strip()}

def main():
    # Configura client OpenAI
    client = OpenAIClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini"
    )
    
    # Crea pipeline DAG
    pipeline = DagPipeline()
    
    # Aggiungi tutti i nodi (coerente con il diagramma)
    pipeline.add_module("data_loader", DataLoader())
    pipeline.add_module("sentiment_analyzer", SentimentAnalyzer(client=client))
    pipeline.add_module("statistics_calculator", StatisticsCalculator())
    pipeline.add_module("metadata_extractor", MetadataExtractor())
    pipeline.add_module("report_generator", ReportGenerator())
    
    # Definisci connessioni (come nel diagramma README)
    # DataLoader -> SentimentAnalyzer
    pipeline.connect(
        source_node="data_loader",
        target_node="sentiment_analyzer",
        source_key="reviews",
        target_key="reviews"
    )
    
    # SentimentAnalyzer -> StatisticsCalculator  
    pipeline.connect(
        source_node="sentiment_analyzer",
        target_node="statistics_calculator",
        source_key="sentiment_results",
        target_key="sentiment_results"
    )
    
    # DataLoader -> MetadataExtractor
    pipeline.connect(
        source_node="data_loader",
        target_node="metadata_extractor",
        source_key="reviews",
        target_key="reviews"
    )
    
    # Tutti convergono in ReportGenerator
    pipeline.connect(
        source_node="sentiment_analyzer",
        target_node="report_generator",
        source_key="sentiment_results",
        target_key="sentiment_results"
    )
    
    pipeline.connect(
        source_node="statistics_calculator",
        target_node="report_generator", 
        source_key="statistics",
        target_key="statistics"
    )
    
    pipeline.connect(
        source_node="metadata_extractor",
        target_node="report_generator",
        source_key="metadata",
        target_key="metadata"
    )
    
    print("🔄 Eseguendo DagPipeline per analisi sentiment...")
    
    # Esegui pipeline
    results = pipeline.run(data={})
    
    # Mostra risultati
    print("✅ Pipeline completata!")
    print("\n" + "="*60)
    print(results["report_generator"]["final_report"])
    
    # Mostra struttura del grafo (coerente con diagramma README)
    print("\n" + "="*60)
    print("🏗️  STRUTTURA DEL GRAFO:")
    print("data_loader ──┬──> sentiment_analyzer ──> statistics_calculator ──┐")
    print("              │                      ↓                          │")
    print("              └──> metadata_extractor ──> report_generator <──────┘")

if __name__ == "__main__":
    main()
