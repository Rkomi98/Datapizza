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
from datapizza.pipeline import FunctionalPipeline, Dependency
from datapizza.core.models import PipelineComponent
from datapizza.clients import OpenAIClient

# Carica variabili d'ambiente
load_dotenv()

# Componenti personalizzati - implementazione completa come nel README
class DataLoader(PipelineComponent):
    """Carica e prepara documenti di esempio."""
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        documents = [
            {"id": 1, "title": "Bug Critical", "content": "Sistema in crash", "priority": "urgent"},
            {"id": 2, "title": "Feature Request", "content": "Nuova funzionalità", "priority": "normal"},
            {"id": 3, "title": "Security Issue", "content": "Vulnerabilità trovata", "priority": "urgent"}
        ]
        return {"documents": documents}
    
    async def _a_run(self, **kwargs) -> Dict[str, Any]:
        documents = [
            {"id": 1, "title": "Bug Critical", "content": "Sistema in crash", "priority": "urgent"},
            {"id": 2, "title": "Feature Request", "content": "Nuova funzionalità", "priority": "normal"},
            {"id": 3, "title": "Security Issue", "content": "Vulnerabilità trovata", "priority": "urgent"}
        ]
        return {"documents": documents}

class Classifier(PipelineComponent):
    """Classifica documenti per urgenza."""
    
    def _run(self, documents, **kwargs) -> Dict[str, Any]:
        # Gestisce sia lista diretta che dizionario dal nodo precedente
        if isinstance(documents, dict) and "documents" in documents:
            doc_list = documents["documents"]
        elif isinstance(documents, list):
            doc_list = documents
        else:
            doc_list = documents
        
        # Classifica documenti per urgenza
        urgent_docs = [d for d in doc_list if d["priority"] == "urgent"]
        has_urgent = len(urgent_docs) > 0
        
        return {
            "classified_documents": doc_list,
            "urgent_documents": urgent_docs,
            "has_urgent": has_urgent
        }
    
    async def _a_run(self, documents, **kwargs) -> Dict[str, Any]:
        # Gestisce sia lista diretta che dizionario dal nodo precedente
        if isinstance(documents, dict) and "documents" in documents:
            doc_list = documents["documents"]
        elif isinstance(documents, list):
            doc_list = documents
        else:
            doc_list = documents
        
        # Classifica documenti per urgenza
        urgent_docs = [d for d in doc_list if d["priority"] == "urgent"]
        has_urgent = len(urgent_docs) > 0
        
        return {
            "classified_documents": doc_list,
            "urgent_documents": urgent_docs,
            "has_urgent": has_urgent
        }

class NotificationSender(PipelineComponent):
    """Invia notifica per documenti urgenti."""
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        return {
            "notification_sent": True,
            "message": "⚠️ Documenti urgenti rilevati! Notifica inviata al team.",
            "timestamp": "2024-01-01T10:00:00Z"
        }
    
    async def _a_run(self, **kwargs) -> Dict[str, Any]:
        return {
            "notification_sent": True,
            "message": "⚠️ Documenti urgenti rilevati! Notifica inviata al team.",
            "timestamp": "2024-01-01T10:00:00Z"
        }

class DocumentProcessor(PipelineComponent):
    """Processa un singolo documento."""
    
    def _run(self, document: Dict, **kwargs) -> Dict[str, Any]:
        # Processa un singolo documento
        processed = {
            **document,
            "processed": True,
            "word_count": len(document["content"].split()),
            "processing_time": "2024-01-01T10:00:00Z"
        }
        return processed
    
    async def _a_run(self, document: Dict, **kwargs) -> Dict[str, Any]:
        # Processa un singolo documento
        processed = {
            **document,
            "processed": True,
            "word_count": len(document["content"].split()),
            "processing_time": "2024-01-01T10:00:00Z"
        }
        return processed

class ReportGenerator(PipelineComponent):
    """Genera report finale."""
    
    def _run(self, classified_documents: List[Dict], **kwargs) -> Dict[str, Any]:
        # Genera report finale
        total = len(classified_documents)
        urgent_count = sum(1 for d in classified_documents if d.get("priority") == "urgent")
        normal_count = total - urgent_count
        
        report = f"""
DOCUMENTO ANALYSIS REPORT
========================
Totale documenti: {total}
Documenti urgenti: {urgent_count}
Documenti normali: {normal_count}

DETTAGLI:
{chr(10).join(f"- {d['title']}: {d['priority']}" for d in classified_documents)}
        """
        
        return {
            "final_report": report.strip(),
            "statistics": {
                "total": total,
                "urgent": urgent_count,
                "normal": normal_count
            }
        }
    
    async def _a_run(self, classified_documents: List[Dict], **kwargs) -> Dict[str, Any]:
        # Genera report finale
        total = len(classified_documents)
        urgent_count = sum(1 for d in classified_documents if d.get("priority") == "urgent")
        normal_count = total - urgent_count
        
        report = f"""
DOCUMENTO ANALYSIS REPORT
========================
Totale documenti: {total}
Documenti urgenti: {urgent_count}
Documenti normali: {normal_count}

DETTAGLI:
{chr(10).join(f"- {d['title']}: {d['priority']}" for d in classified_documents)}
        """
        
        return {
            "final_report": report.strip(),
            "statistics": {
                "total": total,
                "urgent": urgent_count,
                "normal": normal_count
            }
        }

def main():
    # Rimuovo client LLM per semplificare l'esempio come nel README
    
    # Sottopipeline per notifiche (documenti urgenti)
    notification_pipeline = FunctionalPipeline().run(
        name="send_notification",
        node=NotificationSender()
    )
    
    # Sottopipeline per processamento standard (documenti normali)
    standard_processing_pipeline = (
        FunctionalPipeline()
        .foreach(
            name="process_documents",
            dependencies=[Dependency(node_name="classified_documents", target_key=None)],
            do=DocumentProcessor()
        )
        .then(
            name="generate_report",
            node=ReportGenerator(),
            target_key="classified_documents",
            dependencies=[Dependency(node_name="classify", target_key="classified_documents")]
        )
    )
    
    # Pipeline principale con branching condizionale
    pipeline = (
        FunctionalPipeline()
        # Carica documenti
        .run(
            name="load_data", 
            node=DataLoader()
        )
        # Classifica per urgenza
        .then(
            name="classify",
            node=Classifier(),
            target_key="documents"  # Passa risultato di "load_data" come parametro "documents"
        )
        # Branch condizionale basato su presenza documenti urgenti
        .branch(
            condition=lambda ctx: ctx.get("classify", {}).get("has_urgent", False),
            dependencies=[Dependency(node_name="classify")],
            if_true=notification_pipeline,      # Se urgenti -> invia notifica
            if_false=standard_processing_pipeline  # Altrimenti -> processa normalmente
        )
    )
    
    print("🔄 Eseguendo FunctionalPipeline con branching...")
    
    # Esegui pipeline
    results = pipeline.execute()
    
    print("✅ Pipeline completata!")
    
    # Mostra risultati in base al branch eseguito
    if "send_notification" in results:
        print("BRANCH URGENTE ESEGUITO:")
        print(results["send_notification"]["message"])
    else:
        print("BRANCH STANDARD ESEGUITO:")
        print(results["generate_report"]["final_report"])
    
    # Mostra struttura pipeline (coerente con README)
    print("\n" + "="*60)
    print("🏗️  STRUTTURA DELLA PIPELINE:")
    print("load_data → classify → branch")
    print("                        ├─ urgent docs → send_notification")
    print("                        └─ normal docs → foreach → generate_report")

if __name__ == "__main__":
    main()
