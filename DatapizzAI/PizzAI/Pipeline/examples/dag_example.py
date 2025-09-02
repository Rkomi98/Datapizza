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

# Componenti personalizzati per l'esempio
class DataLoader(PipelineComponent):
    """Carica dati di esempio."""
    
    def run(self, **kwargs) -> Dict[str, Any]:
        sample_data = [
            {"id": 1, "text": "Questo prodotto è fantastico! Lo consiglio vivamente.", "user": "Alice"},
            {"id": 2, "text": "Non mi è piaciuto per niente, deludente.", "user": "Bob"},
            {"id": 3, "text": "Prodotto nella media, niente di eccezionale.", "user": "Charlie"},
            {"id": 4, "text": "Servizio clienti eccellente, molto soddisfatto!", "user": "Diana"},
            {"id": 5, "text": "Pessima esperienza, non acquisterò mai più.", "user": "Eve"}
        ]
        return {"reviews": sample_data}

class SentimentAnalyzer(PipelineComponent):
    """Analizza il sentiment dei testi usando LLM."""
    
    def __init__(self, client: OpenAIClient):
        self.client = client
    
    def run(self, reviews: list, **kwargs) -> Dict[str, Any]:
        analyzed_reviews = []
        
        for review in reviews:
            # Prompt per analisi sentiment
            messages = [{
                "role": "user", 
                "content": f"Analizza il sentiment di questo testo e rispondi solo con 'positivo', 'negativo' o 'neutro': '{review['text']}'"
            }]
            
            response = self.client.complete(messages=messages, max_tokens=10)
            sentiment = response.choices[0].message.content.strip().lower()
            
            analyzed_reviews.append({
                **review,
                "sentiment": sentiment
            })
        
        return {"analyzed_reviews": analyzed_reviews}

class StatisticsCalculator(PipelineComponent):
    """Calcola statistiche sui sentiment."""
    
    def run(self, analyzed_reviews: list, **kwargs) -> Dict[str, Any]:
        sentiments = [review["sentiment"] for review in analyzed_reviews]
        
        stats = {
            "total_reviews": len(sentiments),
            "positive_count": sentiments.count("positivo"),
            "negative_count": sentiments.count("negativo"),
            "neutral_count": sentiments.count("neutro")
        }
        
        # Calcola percentuali
        total = stats["total_reviews"]
        stats["positive_percentage"] = (stats["positive_count"] / total) * 100
        stats["negative_percentage"] = (stats["negative_count"] / total) * 100
        stats["neutral_percentage"] = (stats["neutral_count"] / total) * 100
        
        return {"statistics": stats}

class ReportGenerator(PipelineComponent):
    """Genera report finale."""
    
    def run(self, analyzed_reviews: list, statistics: dict, **kwargs) -> Dict[str, Any]:
        report = []
        report.append("=== SENTIMENT ANALYSIS REPORT ===\n")
        
        # Statistiche generali
        stats = statistics
        report.append(f"Totale recensioni: {stats['total_reviews']}")
        report.append(f"Positive: {stats['positive_count']} ({stats['positive_percentage']:.1f}%)")
        report.append(f"Negative: {stats['negative_count']} ({stats['negative_percentage']:.1f}%)")
        report.append(f"Neutrali: {stats['neutral_count']} ({stats['neutral_percentage']:.1f}%)")
        report.append("")
        
        # Dettaglio recensioni
        report.append("=== DETTAGLIO RECENSIONI ===\n")
        for review in analyzed_reviews:
            sentiment_emoji = {"positivo": "😊", "negativo": "😠", "neutro": "😐"}.get(review["sentiment"], "❓")
            report.append(f"👤 {review['user']} {sentiment_emoji}")
            report.append(f"💬 {review['text']}")
            report.append(f"📊 Sentiment: {review['sentiment'].upper()}")
            report.append("-" * 50)
        
        final_report = "\n".join(report)
        
        return {"report": final_report}

def main():
    # Configura client OpenAI
    client = OpenAIClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini"
    )
    
    # Crea pipeline DAG
    pipeline = DagPipeline()
    
    # Aggiungi nodi
    pipeline.add_module("data_loader", DataLoader())
    pipeline.add_module("sentiment_analyzer", SentimentAnalyzer(client=client))
    pipeline.add_module("statistics_calculator", StatisticsCalculator())
    pipeline.add_module("report_generator", ReportGenerator())
    
    # Definisci connessioni (grafo delle dipendenze)
    # data_loader -> sentiment_analyzer
    pipeline.connect(
        source_node="data_loader",
        target_node="sentiment_analyzer", 
        source_key="reviews",
        target_key="reviews"
    )
    
    # sentiment_analyzer -> statistics_calculator
    pipeline.connect(
        source_node="sentiment_analyzer",
        target_node="statistics_calculator",
        source_key="analyzed_reviews", 
        target_key="analyzed_reviews"
    )
    
    # sentiment_analyzer -> report_generator (per le recensioni)
    pipeline.connect(
        source_node="sentiment_analyzer",
        target_node="report_generator",
        source_key="analyzed_reviews",
        target_key="analyzed_reviews"
    )
    
    # statistics_calculator -> report_generator (per le statistiche)
    pipeline.connect(
        source_node="statistics_calculator",
        target_node="report_generator", 
        source_key="statistics",
        target_key="statistics"
    )
    
    print("🔄 Eseguendo DagPipeline per analisi sentiment...")
    
    # Esegui pipeline
    results = pipeline.run(data={})
    
    # Mostra risultati
    print("✅ Pipeline completata!")
    print("\n" + "="*60)
    print(results["report_generator"]["report"])
    
    # Mostra struttura del grafo
    print("\n" + "="*60)
    print("🏗️  STRUTTURA DEL GRAFO:")
    print("data_loader → sentiment_analyzer → statistics_calculator")
    print("                    ↓")
    print("                report_generator")

if __name__ == "__main__":
    main()
