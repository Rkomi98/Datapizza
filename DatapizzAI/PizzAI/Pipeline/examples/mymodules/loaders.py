"""
Moduli di caricamento dati per esempi YAML.
"""

from typing import Any, Dict, List
from datapizzai.core.models import PipelineComponent


class DocumentLoader(PipelineComponent):
    """Carica documenti di esempio per il test YAML."""
    
    def __init__(self, source: str = "default"):
        self.source = source
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        # Simula caricamento documenti da diverse fonti
        if self.source == "test":
            documents = [
                {"id": 1, "title": "Test Document 1", "content": "Contenuto del primo documento di test"},
                {"id": 2, "title": "Test Document 2", "content": "Contenuto del secondo documento di test"}
            ]
        else:
            documents = [
                {"id": 1, "title": "YAML Example", "content": "Questo documento viene caricato da configurazione YAML"},
                {"id": 2, "title": "Pipeline Demo", "content": "Dimostrazione di FunctionalPipeline con YAML"},
                {"id": 3, "title": "Datapizzai Test", "content": "Test della libreria datapizzai con moduli esterni"}
            ]
        
        return {
            "documents": documents,
            "source": self.source,
            "count": len(documents)
        }
    
    async def _a_run(self, **kwargs) -> Dict[str, Any]:
        return self._run(**kwargs)


class CSVLoader(PipelineComponent):
    """Carica dati da file CSV simulato."""
    
    def __init__(self, file_path: str, delimiter: str = ","):
        self.file_path = file_path
        self.delimiter = delimiter
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        # Simula lettura CSV
        data = [
            {"name": "Alice", "age": 30, "city": "Milano"},
            {"name": "Bob", "age": 25, "city": "Roma"},
            {"name": "Charlie", "age": 35, "city": "Napoli"}
        ]
        
        return {
            "csv_data": data,
            "file_path": self.file_path,
            "delimiter": self.delimiter,
            "rows": len(data)
        }
    
    async def _a_run(self, **kwargs) -> Dict[str, Any]:
        return self._run(**kwargs)
