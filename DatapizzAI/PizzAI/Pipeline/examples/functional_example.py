#!/usr/bin/env python3
"""
Esempio di utilizzo di FunctionalPipeline per processare e analizzare documenti
con supporto per branching condizionale e cicli.

Requisiti:
- pip install python-dotenv
- .env con OPENAI_API_KEY
"""

import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from datapizzai.pipeline import FunctionalPipeline, Dependency
from datapizzai.core.models import PipelineComponent
from datapizzai.clients import OpenAIClient

# Carica variabili d'ambiente
load_dotenv()

# Componenti personalizzati per l'esempio
class DocumentLoader(PipelineComponent):
    """Carica e prepara documenti di esempio."""
    
    def run(self, **kwargs) -> Dict[str, Any]:
        documents = [
            {
                "id": 1,
                "title": "Guida Python",
                "content": "Python è un linguaggio di programmazione versatile e potente, ideale per principianti.",
                "category": "programming"
            },
            {
                "id": 2, 
                "title": "Ricetta Carbonara",
                "content": "La carbonara è un piatto tradizionale romano con uova, pecorino e guanciale.",
                "category": "cooking"
            },
            {
                "id": 3,
                "title": "Machine Learning Basics", 
                "content": "Il machine learning è una branca dell'intelligenza artificiale che permette ai computer di imparare.",
                "category": "programming"
            }
        ]
        
        return {"documents": documents}

class DocumentClassifier(PipelineComponent):
    """Classifica documenti usando LLM."""
    
    def __init__(self, client: OpenAIClient):
        self.client = client
    
    def run(self, documents: List[Dict], **kwargs) -> Dict[str, Any]:
        classified_docs = []
        
        for doc in documents:
            # Usa LLM per classificazione più accurata
            messages = [{
                "role": "user",
                "content": f"Classifica questo documento in una di queste categorie: 'technical', 'lifestyle', 'educational'. Rispondi solo con la categoria.\n\nTitolo: {doc['title']}\nContenuto: {doc['content']}"
            }]
            
            response = self.client.complete(messages=messages, max_tokens=10)
            ai_category = response.choices[0].message.content.strip().lower()
            
            classified_docs.append({
                **doc,
                "ai_category": ai_category
            })
        
        return {"classified_documents": classified_docs}

class TechnicalDocumentProcessor(PipelineComponent):
    """Processa specificamente documenti tecnici."""
    
    def __init__(self, client: OpenAIClient):
        self.client = client
    
    def run(self, document: Dict, **kwargs) -> Dict[str, Any]:
        # Genera keywords tecniche
        messages = [{
            "role": "user", 
            "content": f"Estrai 3-5 keywords tecniche da questo documento:\n{document['content']}\nRispondi con una lista separata da virgole."
        }]
        
        response = self.client.complete(messages=messages, max_tokens=50)
        keywords = [kw.strip() for kw in response.choices[0].message.content.split(",")]
        
        return {
            **document,
            "technical_keywords": keywords,
            "processed_by": "TechnicalProcessor"
        }

class GeneralDocumentProcessor(PipelineComponent):
    """Processa documenti generali."""
    
    def run(self, document: Dict, **kwargs) -> Dict[str, Any]:
        return {
            **document,
            "word_count": len(document["content"].split()),
            "processed_by": "GeneralProcessor"
        }

class KeywordNormalizer(PipelineComponent):
    """Normalizza keywords (usato nel foreach)."""
    
    def run(self, keyword: str, **kwargs) -> str:
        return keyword.lower().strip()

class ReportBuilder(PipelineComponent):
    """Costruisce report finale."""
    
    def run(self, classified_documents: List[Dict], **kwargs) -> Dict[str, Any]:
        report = []
        report.append("=== DOCUMENT ANALYSIS REPORT ===\n")
        
        # Statistiche per categoria
        categories = {}
        for doc in classified_documents:
            cat = doc.get("ai_category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        report.append("📊 CATEGORIA DISTRIBUTION:")
        for cat, count in categories.items():
            report.append(f"  {cat}: {count} documenti")
        report.append("")
        
        # Dettaglio documenti
        report.append("📄 DOCUMENT DETAILS:")
        for doc in classified_documents:
            report.append(f"\n🔸 {doc['title']}")
            report.append(f"   Categoria AI: {doc['ai_category']}")
            report.append(f"   Processato da: {doc.get('processed_by', 'N/A')}")
            
            if "technical_keywords" in doc:
                report.append(f"   Keywords tecniche: {', '.join(doc['technical_keywords'])}")
            if "word_count" in doc:
                report.append(f"   Parole: {doc['word_count']}")
        
        final_report = "\n".join(report)
        return {"report": final_report}

class SendNotification(PipelineComponent):
    """Invia notifica per documenti tecnici."""
    
    def run(self, **kwargs) -> Dict[str, Any]:
        return {"notification_sent": True, "message": "Nuovo documento tecnico rilevato!"}

def main():
    # Configura client
    client = OpenAIClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini"
    )
    
    # Sottopipeline per notifica (documenti tecnici)
    notification_pipeline = FunctionalPipeline().run(
        name="send_notification",
        node=SendNotification()
    )
    
    # Sottopipeline per processamento generale
    general_processing = (
        FunctionalPipeline()
        .foreach(
            name="process_general",
            dependencies=[Dependency(node_name="classified_documents")],
            do=GeneralDocumentProcessor()
        )
        .then(
            name="build_report",
            node=ReportBuilder(),
            target_key="classified_documents",
            dependencies=[Dependency(node_name="classify")]
        )
    )
    
    # Pipeline principale
    pipeline = (
        FunctionalPipeline()
        # 1. Carica documenti
        .run(
            name="load_documents",
            node=DocumentLoader()
        )
        # 2. Classifica con AI
        .then(
            name="classify", 
            node=DocumentClassifier(client=client),
            target_key="documents"
        )
        # 3. Branch condizionale basato su presenza di documenti tecnici
        .branch(
            condition=lambda ctx: any(
                doc.get("ai_category") == "technical" 
                for doc in ctx.get("classify", {}).get("classified_documents", [])
            ),
            dependencies=[Dependency(node_name="classify")],
            if_true=notification_pipeline,  # Se ci sono doc tecnici -> notifica
            if_false=general_processing     # Altrimenti -> processamento normale
        )
    )
    
    print("🔄 Eseguendo FunctionalPipeline con branching...")
    
    # Esegui pipeline
    results = pipeline.execute()
    
    print("✅ Pipeline completata!")
    
    # Mostra risultati
    if "send_notification" in results:
        print(f"\n🔔 {results['send_notification']['message']}")
    
    if "build_report" in results:
        print(f"\n{results['build_report']['report']}")
    
    # Mostra struttura pipeline
    print("\n" + "="*60)
    print("🏗️  STRUTTURA DELLA PIPELINE:")
    print("load_documents → classify → branch")
    print("                              ├─ technical docs → send_notification")
    print("                              └─ other docs → foreach → build_report")

if __name__ == "__main__":
    main()
