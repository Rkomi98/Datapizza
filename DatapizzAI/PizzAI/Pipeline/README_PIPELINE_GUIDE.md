# Guida alle pipeline DatapizzAI

Questa guida fornisce esempi pratici per utilizzare le tre tipologie di pipeline disponibili in DatapizzAI:

- **IngestionPipeline**: per processare e ingerire documenti in vector stores
- **DagPipeline**: per creare grafi di dipendenze tra componenti  
- **FunctionalPipeline**: per pipeline funzionali con branching, cicli e dipendenze

## Indice

- [1. Ingestion pipeline](#1-ingestion-pipeline)
  - [Descrizione](#descrizione)
  - [Componenti principali](#componenti-principali)
  - [Esempio pratico](#esempio-pratico)
  - [Diagramma di flusso](#diagramma-di-flusso)
  - [Script completo](#script-completo)
- [2. Dag pipeline](#2-dag-pipeline)
  - [Descrizione](#descrizione-1)
  - [Caratteristiche principali](#caratteristiche-principali)
  - [Esempio pratico](#esempio-pratico-1)
  - [Diagramma di flusso](#diagramma-di-flusso-1)
  - [Script completo](#script-completo-1)
- [3. Functional pipeline](#3-functional-pipeline)
  - [Descrizione](#descrizione-2)
  - [Caratteristiche avanzate](#caratteristiche-avanzate)
  - [Esempio pratico](#esempio-pratico-2)
  - [Diagramma di flusso](#diagramma-di-flusso-2)
  - [Script completo](#script-completo-2)
- [Configurazione YAML](#configurazione-yaml)
  - [Esempio per DagPipeline](#esempio-per-dagpipeline)
  - [Esempio per FunctionalPipeline](#esempio-per-functionalpipeline)
- [Confronto delle pipeline](#confronto-delle-pipeline)
- [Best practices](#best-practices)
  - [Scelta della pipeline](#scelta-della-pipeline)
  - [Gestione degli errori](#gestione-degli-errori)
  - [Performance](#performance)
- [Esempi completi](#esempi-completi)

## 1. Ingestion pipeline

### Descrizione

L'IngestionPipeline è progettata per processare documenti e ingerirli in vector stores. È ideale per costruire knowledge bases e sistemi RAG.

### Componenti principali

- **Parser**: estrazione del contenuto dai documenti
- **Splitter**: divisione del contenuto in chunks
- **Embedder**: generazione di embeddings vettoriali
- **Vector store**: archiviazione dei chunks con embeddings

### Esempio pratico

```python
import os
from dotenv import load_dotenv
from datapizzai.pipeline import IngestionPipeline
from datapizzai.modules.splitters import TextSplitter
from datapizzai.embedders import NodeEmbedder
from datapizzai.clients import OpenAIClient
from datapizzai.core.models import PipelineComponent

load_dotenv()

# Componente personalizzato per leggere file di testo
class FileReader(PipelineComponent):
    def _run(self, file_path: str, **kwargs) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def _a_run(self, file_path: str, **kwargs) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

# 1. Configura client per embeddings  
client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"), 
    model="text-embedding-3-small"  # Modello per embeddings
)

# 2. Definisci componenti della pipeline in ordine di esecuzione
components = [
    FileReader(),          # Legge il contenuto del file
    TextSplitter(
        max_char=200,      # Dimensione massima di ogni chunk in caratteri
        overlap=50         # Sovrapposizione tra chunks consecutivi
    ),
    NodeEmbedder(
        client=client,                    # Client per generare embeddings
        model_name="text-embedding-3-small"  # Nome del modello embedding
    )
]

# 3. Crea pipeline senza vector store (restituisce chunks processati)
pipeline = IngestionPipeline(
    modules=components,    # Lista dei componenti da eseguire
    vector_store=None,     # None = non salva automaticamente
    collection_name=None   # Nome collezione nel vector store (non usato se vector_store=None)
)

# 4. Esegui processamento con metadata opzionale
chunks = pipeline.run(
    file_path="document.txt",            # Percorso del documento da processare
    metadata={"source": "esempio"}      # Metadata aggiuntivo da allegare ai chunks (OPZIONALE)
)

# Il risultato è una lista di oggetti Chunk con testo, embeddings e metadata
print(f"Generati {len(chunks)} chunks dal documento")
```

### Note importanti

Ci sono alcune precisazioni che pensiamo siano importanti prima di procedere alla prossima tipologia di Pipeline:
- **NodeEmbedder vs ClientEmbedder**: usa `NodeEmbedder` nelle pipeline perché lavora con liste di oggetti `Chunk`. `ClientEmbedder` è per singole stringhe.
- **Metadata**: vengono applicati dall'`IngestionPipeline.run()` dopo la creazione dei chunks, non durante lo splitting
- **Embeddings**: `NodeEmbedder` aggiunge gli embeddings agli oggetti `Chunk` esistenti, non crea nuovi oggetti

### Diagramma di flusso

![Ingestion Pipeline Flow](ingestion-pipeline-flow.svg)

### Script completo

Vedi `examples/ingestion_example.py` per un esempio completo funzionante.

## 2. Dag pipeline

### Descrizione

La DagPipeline permette di creare grafi di dipendenze (DAG - Directed Acyclic Graph) tra componenti, dove ogni nodo può dipendere dai risultati di nodi precedenti.

### Caratteristiche principali

- **Nodi**: componenti che eseguono operazioni specifiche
- **Connessioni**: definiscono le dipendenze tra nodi
- **Esecuzione parallela**: nodi indipendenti vengono eseguiti in parallelo
- **Gestione degli errori**: propagazione controllata degli errori nel grafo

### Esempio pratico

```python
from datapizzai.pipeline import DagPipeline
from datapizzai.core.models import PipelineComponent

# 1. Definisci tutti i componenti del grafo
class DataLoader(PipelineComponent):
    def _run(self, **kwargs):
        return {"reviews": ["Prodotto eccellente!", "Non mi piace", "Nella media"]}
    async def _a_run(self, **kwargs):
        return self._run(**kwargs)

class SentimentAnalyzer(PipelineComponent):
    def _run(self, reviews, **kwargs):
        # Simula analisi sentiment
        analyzed = [{"text": r, "sentiment": "positive" if "eccellente" in r else "negative" if "non" in r.lower() else "neutral"} for r in reviews]
        return {"sentiment_results": analyzed}
    async def _a_run(self, reviews, **kwargs):
        return self._run(reviews=reviews, **kwargs)

class StatisticsCalculator(PipelineComponent):
    def _run(self, sentiment_results, **kwargs):
        sentiments = [r["sentiment"] for r in sentiment_results]
        stats = {
            "positive": sentiments.count("positive"),
            "negative": sentiments.count("negative"), 
            "neutral": sentiments.count("neutral")
        }
        return {"statistics": stats}
    async def _a_run(self, sentiment_results, **kwargs):
        return self._run(sentiment_results=sentiment_results, **kwargs)

class MetadataExtractor(PipelineComponent):
    def _run(self, reviews, **kwargs):
        metadata = {
            "total_reviews": len(reviews),
            "avg_length": sum(len(r) for r in reviews) / len(reviews),
            "timestamp": "2025-09-15"
        }
        return {"metadata": metadata}
    async def _a_run(self, reviews, **kwargs):
        return self._run(reviews=reviews, **kwargs)

class ReportGenerator(PipelineComponent):
    def _run(self, sentiment_results, statistics, metadata, **kwargs):
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
    async def _a_run(self, sentiment_results, statistics, metadata, **kwargs):
        return self._run(sentiment_results=sentiment_results, statistics=statistics, metadata=metadata, **kwargs)

# 2. Crea pipeline DAG
pipeline = DagPipeline()

# 3. Aggiungi tutti i nodi
pipeline.add_module("data_loader", DataLoader())
pipeline.add_module("sentiment_analyzer", SentimentAnalyzer())
pipeline.add_module("statistics_calculator", StatisticsCalculator())
pipeline.add_module("metadata_extractor", MetadataExtractor())
pipeline.add_module("report_generator", ReportGenerator())

# 4. Definisci connessioni (come nel diagramma)
# DataLoader -> SentimentAnalyzer
pipeline.connect(
    source_node="data_loader",
    target_node="sentiment_analyzer",
    source_key="reviews",      # Chiave nel risultato del nodo sorgente
    target_key="reviews"       # Parametro del nodo destinazione
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

# 5. Esegui pipeline
results = pipeline.run({})
print(results["report_generator"]["final_report"])
```

### Diagramma di flusso

![DAG Pipeline Flow](dag-pipeline-flow.svg)

### Script completo

Vedi `examples/dag_example.py` per un esempio di analisi sentiment con grafo delle dipendenze.

## 3. Functional pipeline

### Descrizione

La FunctionalPipeline offre un approccio funzionale alla costruzione di pipeline con supporto per branching condizionale, cicli e dipendenze complesse.

### Caratteristiche avanzate

- **Branching**: esecuzione condizionale di sottopipeline
- **Foreach**: iterazione su collezioni di dati
- **Dipendenze**: gestione esplicita delle dipendenze tra nodi
- **Composizione**: combinazione di pipeline complesse

### Esempio pratico

```python
from datapizzai.pipeline import FunctionalPipeline, Dependency
from datapizzai.core.models import PipelineComponent

# 1. Definisci tutti i componenti necessari
class DataLoader(PipelineComponent):
    def _run(self, **kwargs):
        documents = [
            {"id": 1, "title": "Bug Critical", "content": "Sistema in crash", "priority": "urgent"},
            {"id": 2, "title": "Feature Request", "content": "Nuova funzionalità", "priority": "normal"},
            {"id": 3, "title": "Security Issue", "content": "Vulnerabilità trovata", "priority": "urgent"}
        ]
        return {"documents": documents}
    async def _a_run(self, **kwargs):
        return self._run(**kwargs)

class Classifier(PipelineComponent):
    def _run(self, documents, **kwargs):
        # Accetta sia dict {"documents": [...]} sia lista di dict
        if isinstance(documents, dict) and "documents" in documents:
            documents = documents["documents"]
        elif documents is None:
            documents = []
        
        # Classifica documenti per urgenza
        urgent_docs = [d for d in documents if isinstance(d, dict) and d.get("priority") == "urgent"]
        has_urgent = len(urgent_docs) > 0
        
        return {
            "classified_documents": documents,
            "urgent_documents": urgent_docs,
            "has_urgent": has_urgent
        }
    async def _a_run(self, documents, **kwargs):
        return self._run(documents=documents, **kwargs)

class NotificationSender(PipelineComponent):
    def _run(self, **kwargs):
        return {
            "notification_sent": True,
            "message": "⚠️ Documenti urgenti rilevati! Notifica inviata al team.",
            "timestamp": "2025-09-15T10:00:00Z"
        }
    async def _a_run(self, **kwargs):
        return self._run(**kwargs)

class DocumentProcessor(PipelineComponent):
    def _run(self, document, **kwargs):
        # Processa un singolo documento
        processed = {
            **document,
            "processed": True,
            "word_count": len(document["content"].split()),
            "processing_time": "2025-09-15T10:00:00Z"
        }
        return processed
    async def _a_run(self, document, **kwargs):
        return self._run(document=document, **kwargs)

class ReportGenerator(PipelineComponent):
    def _run(self, classified_documents, **kwargs):
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
    async def _a_run(self, classified_documents, **kwargs):
        return self._run(classified_documents=classified_documents, **kwargs)

# 2. Crea sottopipeline per notifiche (documenti urgenti)
notification_pipeline = FunctionalPipeline().run(
    name="send_notification",
    node=NotificationSender()
)

# 3. Crea sottopipeline per processamento standard (documenti normali)
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

# 4. Pipeline principale con branching condizionale
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

# 5. Esegui pipeline
results = pipeline.execute()

# 6. Mostra risultati in base al branch eseguito
if "send_notification" in results:
    print("BRANCH URGENTE ESEGUITO:")
    print(results["send_notification"]["message"])
else:
    print("BRANCH STANDARD ESEGUITO:")
    print(results["generate_report"]["final_report"])
```

### Note sul flusso dati

- **Passaggio dati**: nella FunctionalPipeline, `target_key="documents"` passa l'INTERO risultato del nodo precedente (es. `{"documents": [...]}`) al parametro `documents` del nodo successivo
- **Gestione input**: i componenti devono gestire sia dizionari che liste come input per essere flessibili
- **Context access**: usa `lambda ctx: ctx.get("node_name", {}).get("key")` per accedere ai dati nel branching

### Diagramma di flusso

![Functional Pipeline Flow](functional-pipeline-flow.svg)

### Script completo

Vedi `examples/functional_example.py` per un esempio completo con branching e foreach.

## Configurazione YAML

Tutte le pipeline supportano la configurazione tramite file YAML per maggiore flessibilità e riutilizzo.

### Esempio per DagPipeline

Caricamento e utilizzo di DagPipeline da configurazione YAML:

```python
import os
import sys
from datapizzai.pipeline import DagPipeline

# Setup path per trovare mymodules (necessario per notebook)
examples_dir = "/home/mcalcaterra/Documenti/GitHub/Datapizza/DatapizzAI/PizzAI/Pipeline/examples"
sys.path.insert(0, examples_dir)

# Crea istanza DagPipeline e carica configurazione YAML
dag_pipeline = DagPipeline()
dag_pipeline.from_yaml(os.path.join(examples_dir, "dag_config.yaml"))

# Esegui pipeline (dati generati automaticamente dai moduli)
results = dag_pipeline.run({})

# Accedi ai risultati di ogni nodo
print(f"Nodi eseguiti: {list(results.keys())}")
for node_name, result in results.items():
    print(f"{node_name}: {result}")
```

Il file YAML `examples/dag_config.yaml` definisce moduli personalizzati (`DocumentLoader`, `TextProcessor`) e le loro connessioni automatiche.

**Esecuzione**:
```bash
cd Pipeline/examples
python3 dag_yaml_example.py
```

#### Diagramma flusso DagPipeline YAML

![DAG YAML Pipeline Flow](dag-yaml-pipeline-flow.svg)

### Esempio per FunctionalPipeline

Caricamento e utilizzo di FunctionalPipeline da configurazione YAML:

```python
import os
import sys
from datapizzai.pipeline import FunctionalPipeline

# Setup path per trovare mymodules (necessario per notebook)
examples_dir = "/home/mcalcaterra/Documenti/GitHub/Datapizza/DatapizzAI/PizzAI/Pipeline/examples"
sys.path.insert(0, examples_dir)

# Carica pipeline funzionale da file YAML
pipeline = FunctionalPipeline.from_yaml(os.path.join(examples_dir, "functional_pipeline_config.yaml"))

# Esegui pipeline completa
results = pipeline.execute()

# Mostra risultati del flusso
if "build_report" in results:
    print(results["build_report"]["final_report"])
else:
    print("Pipeline completata con successo!")

print(f"Moduli eseguiti: {list(results.keys())}")
```

Il file YAML definisce moduli esterni (`DocumentLoader`, `TextProcessor`, `DataValidator`, `ReportBuilder`) e le dipendenze tra step con `target_key`.

#### Diagramma flusso FunctionalPipeline YAML

![Functional YAML Pipeline Flow](functional-yaml-pipeline-flow.svg)

## Confronto delle pipeline

| Caratteristica | IngestionPipeline | DagPipeline | FunctionalPipeline |
|---------------|-------------------|-------------|-------------------|
| **Caso d'uso** | Processamento documenti | Grafi dipendenze | Pipeline complesse |
| **Complessità** | Bassa | Media | Alta |
| **Branching** | No | No | Sì |
| **Cicli** | No | No | Sì (foreach) |
| **Parallellismo** | Sequenziale | Automatico | Controllato |
| **Vector store** | Integrato | Manuale | Manuale |

## Best practices

### Scelta della pipeline

- **IngestionPipeline**: per RAG, knowledge bases, processamento documenti
- **DagPipeline**: per workflow con dipendenze complesse, analisi multi-step  
- **FunctionalPipeline**: per logica di business complessa, routing condizionale

### Gestione degli errori

```python
# Sempre gestire eccezioni nei componenti
class SafeProcessor(PipelineComponent):
    def _run(self, **kwargs):
        try:
            return self.process_data(kwargs)
        except Exception as e:
            return {"error": str(e), "success": False}
    async def _a_run(self, **kwargs):
        return self._run(**kwargs)
```

### Performance

- Usa componenti asincroni quando possibile
- Minimizza le dipendenze nelle DagPipeline
- Cache risultati intermedi per pipeline complesse

## Esempi completi

Gli script di esempio completi e funzionanti sono disponibili in:

- `examples/ingestion_example.py` - IngestionPipeline con FileReader e TextSplitter
- `examples/dag_example.py` - DagPipeline con grafo complesso a 5 nodi
- `examples/dag_yaml_example.py` - DagPipeline caricata da YAML con moduli esterni
- `examples/functional_example.py` - FunctionalPipeline con branching condizionale
- `examples/yaml_pipeline_example.py` - FunctionalPipeline caricata da YAML con moduli esterni

### File di supporto

- `examples/dag_config.yaml` - Configurazione YAML esterna per `dag_yaml_example.py`
- `examples/functional_pipeline_config.yaml` - Configurazione YAML esterna per `yaml_pipeline_example.py`
- `examples/mymodules/` - Moduli personalizzati caricati via YAML:
  - `loaders.py` - DocumentLoader e CSVLoader
  - `processors.py` - TextProcessor, DataValidator, ReportBuilder

Ogni script include dati di esempio e può essere eseguito direttamente. L'esempio YAML dimostra come separare configurazione dal codice Python.

### Test rapido di tutti gli esempi

```bash
cd Pipeline/examples

# Test IngestionPipeline (richiede API key)
python3 ingestion_example.py

# Test DagPipeline (richiede API key per SentimentAnalyzer)
python3 dag_example.py

# Test DagPipeline con YAML (autocontenuto, nessuna API key richiesta)
python3 dag_yaml_example.py

# Test FunctionalPipeline (richiede API key)
python3 functional_example.py

# Test FunctionalPipeline con YAML (autocontenuto, nessuna API key richiesta)
python3 yaml_pipeline_example.py
```
