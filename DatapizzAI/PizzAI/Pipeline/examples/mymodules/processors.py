"""
Moduli di processamento dati per esempi YAML.
"""

from typing import Any, Dict, List
from datapizza.core.models import PipelineComponent


class TextProcessor(PipelineComponent):
    """Processa documenti di testo."""
    
    def __init__(self, min_length: int = 10, add_metadata: bool = True):
        self.min_length = min_length
        self.add_metadata = add_metadata
    
    def _run(self, documents, **kwargs) -> Dict[str, Any]:
        # Gestisce input flessibile come negli altri esempi
        if isinstance(documents, dict) and "documents" in documents:
            doc_list = documents["documents"]
        elif isinstance(documents, list):
            doc_list = documents
        else:
            doc_list = documents
        
        processed_docs = []
        
        for doc in doc_list:
            processed_doc = doc.copy()
            
            # Aggiungi conteggio parole
            word_count = len(doc["content"].split())
            processed_doc["word_count"] = word_count
            
            # Filtra documenti troppo corti
            if word_count >= self.min_length:
                processed_doc["status"] = "valid"
            else:
                processed_doc["status"] = "too_short"
            
            # Aggiungi metadata se richiesto
            if self.add_metadata:
                processed_doc["processed_by"] = "TextProcessor"
                processed_doc["char_count"] = len(doc["content"])
                processed_doc["has_numbers"] = any(char.isdigit() for char in doc["content"])
            
            processed_docs.append(processed_doc)
        
        # Statistiche di processamento
        valid_count = sum(1 for doc in processed_docs if doc["status"] == "valid")
        
        return {
            "processed_documents": processed_docs,
            "total_processed": len(processed_docs),
            "valid_documents": valid_count,
            "filtered_out": len(processed_docs) - valid_count,
            "processor_config": {
                "min_length": self.min_length,
                "add_metadata": self.add_metadata
            }
        }
    
    async def _a_run(self, documents, **kwargs) -> Dict[str, Any]:
        return self._run(documents=documents, **kwargs)


class DataValidator(PipelineComponent):
    """Valida struttura dei dati."""
    
    def __init__(self, required_fields: List[str] = None):
        self.required_fields = required_fields or ["id", "title", "content"]
    
    def _run(self, processed_documents, **kwargs) -> Dict[str, Any]:
        # Estrae documenti dall'input
        if isinstance(processed_documents, dict) and "processed_documents" in processed_documents:
            docs = processed_documents["processed_documents"]
        else:
            docs = processed_documents
        
        validation_results = []
        valid_docs = []
        
        for doc in docs:
            validation = {
                "document_id": doc.get("id", "unknown"),
                "is_valid": True,
                "missing_fields": [],
                "errors": []
            }
            
            # Controlla campi richiesti
            for field in self.required_fields:
                if field not in doc:
                    validation["missing_fields"].append(field)
                    validation["is_valid"] = False
            
            # Validazioni specifiche
            if "word_count" in doc and doc["word_count"] == 0:
                validation["errors"].append("Empty content")
                validation["is_valid"] = False
            
            validation_results.append(validation)
            
            if validation["is_valid"]:
                valid_docs.append(doc)
        
        return {
            "validation_results": validation_results,
            "valid_documents": valid_docs,
            "validation_summary": {
                "total_checked": len(docs),
                "valid_count": len(valid_docs),
                "invalid_count": len(docs) - len(valid_docs),
                "required_fields": self.required_fields
            }
        }
    
    async def _a_run(self, processed_documents, **kwargs) -> Dict[str, Any]:
        return self._run(processed_documents=processed_documents, **kwargs)


class ReportBuilder(PipelineComponent):
    """Costruisce report finale dai dati validati."""
    
    def _run(self, validation_results, **kwargs) -> Dict[str, Any]:
        # Estrae risultati di validazione
        if isinstance(validation_results, dict):
            if "validation_results" in validation_results:
                results = validation_results["validation_results"]
                summary = validation_results.get("validation_summary", {})
                valid_docs = validation_results.get("valid_documents", [])
            else:
                results = [validation_results]
                summary = {}
                valid_docs = []
        else:
            results = validation_results
            summary = {}
            valid_docs = []
        
        # Costruisci report dettagliato
        report_lines = []
        report_lines.append("=== YAML PIPELINE PROCESSING REPORT ===")
        report_lines.append("")
        
        # Sommario
        if summary:
            report_lines.append("📊 SUMMARY:")
            report_lines.append(f"   Total documents: {summary.get('total_checked', 0)}")
            report_lines.append(f"   Valid: {summary.get('valid_count', 0)}")
            report_lines.append(f"   Invalid: {summary.get('invalid_count', 0)}")
            report_lines.append("")
        
        # Dettagli documenti validi
        if valid_docs:
            report_lines.append("✅ VALID DOCUMENTS:")
            for doc in valid_docs[:3]:  # Limita a primi 3 per brevità
                report_lines.append(f"   • {doc.get('title', 'Untitled')} ({doc.get('word_count', 0)} words)")
            if len(valid_docs) > 3:
                report_lines.append(f"   ... and {len(valid_docs) - 3} more")
            report_lines.append("")
        
        # Errori di validazione
        invalid_results = [r for r in results if not r.get("is_valid", True)]
        if invalid_results:
            report_lines.append("❌ VALIDATION ERRORS:")
            for result in invalid_results:
                doc_id = result.get("document_id", "unknown")
                errors = result.get("missing_fields", []) + result.get("errors", [])
                report_lines.append(f"   • Document {doc_id}: {', '.join(errors)}")
            report_lines.append("")
        
        report_lines.append("Pipeline completed successfully via YAML configuration! 🚀")
        
        final_report = "\n".join(report_lines)
        
        return {
            "final_report": final_report,
            "report_metadata": {
                "generated_by": "ReportBuilder",
                "total_lines": len(report_lines),
                "documents_processed": len(results)
            }
        }
    
    async def _a_run(self, validation_results, **kwargs) -> Dict[str, Any]:
        return self._run(validation_results=validation_results, **kwargs)
