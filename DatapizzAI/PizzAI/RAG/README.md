# RAG con datapizza-ai - Quick start

Implementazione rapida di un sistema RAG utilizzando la libreria datapizza-ai.

## File disponibili

- `AZURE_SERVICES_GUIDE.md` - **LEGGI PRIMA**: Differenze tra servizi Azure
- `test_azure_openai.py` - **TEST FIRST**: Verifica configurazione Azure OpenAI
- `text_parser_example.py` - **NUOVO**: Esempio con TextParser (più semplice)
- `improved_treebuilder_example.py` - **NUOVO**: Risolve errori TreeBuilder
- `fix_api_key_issue.py` - **DIAGNOSTIC**: Risolve problemi API key
- `env.example` - Template configurazione con tutte le opzioni
- `simple_rag_example.py` - **START HERE**: Esempio funzionante solo con Azure OpenAI
- `README_RAG_COMPLETE_GUIDE.md` - Guida completa aggiornata con TextParser
- `rag_example.py` - Esempio completo con Azure Document Intelligence
- `component_examples.py` - Esempi specifici per ogni componente
- `azure_openai_config.example.env` - Configurazione solo Azure OpenAI
- `config.example.json` - File di configurazione completo

## ⚠️ Problema comune: servizi Azure

Se ottieni errore `ResourceNotFoundError (404)` con `AzureParser`, è perché stai confondendo:
- **Azure OpenAI** (GPT, embedding) ← quello che probabilmente hai
- **Azure Document Intelligence** (parsing PDF) ← servizio separato richiesto da AzureParser

**Soluzione rapida**: usa `simple_rag_example.py` che funziona solo con Azure OpenAI.

## Setup rapido

### 1. Prerequisiti

```bash
pip install datapizza-ai
# Installare anche le dipendenze per i servizi utilizzati (OpenAI, Azure, Cohere, Qdrant)
```

### 2. Configurazione

```bash
# Copia il template e inserisci le tue API key
cp env.example .env

# O usa il diagnostic tool
python fix_api_key_issue.py
```

### 3. Avvio Qdrant (locale)

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 4. Test configurazione

```bash
# Prima testa che tutto funzioni
python test_azure_openai.py

# Se tutti i test passano, prova l'esempio
python simple_rag_example.py
```

## Flusso base

1. **Parse** documenti → struttura gerarchica
2. **Caption** immagini/tabelle → descrizioni testuali  
3. **Split** testo → chunk gestibili
4. **Embed** chunk → vettori numerici
5. **Store** nel vector database
6. **Query** → retrieval + generazione risposta

## Componenti principali

| Componente | Descrizione | Obbligatorio |
|------------|-------------|-------------|
| Parser | Estrazione strutturata da PDF/documenti | ✅ |
| Captioner | Descrizione di immagini e tabelle | ✅ |
| Splitter | Divisione in chunk | ✅ |
| Embedder | Conversione in vettori | ✅ |
| VectorStore | Database vettoriale | ✅ |
| TreeBuilder | Ristrutturazione gerarchica | ⚠️ Facoltativo |
| Metatagger | Aggiunta metadati e tag | ⚠️ Facoltativo |
| Reranker | Riordino risultati per rilevanza | ⚠️ Facoltativo |
| PromptTemplate | Template per generazione | ⚠️ Facoltativo |

## Esempio minimo con TextParser

```python
from datapizza.clients import OpenAIClient


# Testo di esempio
text = """Il machine learning è una branca dell'intelligenza artificiale.

Permette ai computer di apprendere dai dati senza essere programmati esplicitamente.
Utilizza algoritmi statistici per identificare pattern nei dati."""

# Setup
client = OpenAIClient(api_key="your_key")
splitter = TextSplitter(max_char=500, overlap=50)
embedder = NodeEmbedder(client=client, model_name="text-embedding-3-small")
vectorstore = QdrantVectorstore(host="localhost")

# Processo
document = parse_text(text)  # Parser semplice per testo
chunks = splitter.invoke(text)  # Usa direttamente il testo
embedded_chunks = embedder.invoke(chunks)

# Storage
for chunk in embedded_chunks:
    vectorstore.add(chunk, collection_name="docs")
```

## Problemi comuni TreeBuilder

### 1. TypeError (risolto)
**NON** passare il nodo ma il testo:

```python
# ❌ SBAGLIATO (causa TypeError)
restructured_node = tree_builder.invoke(document_node)

# ✅ CORRETTO
restructured_node = tree_builder.build_tree(text)
```

### 2. XML parsing failed
Se vedi errori come `XML parsing failed after cleaning`, l'LLM non produce XML valido:

### 3. API key non valida (nuovo)
Se vedi errori come `Error code: 401 - invalid_api_key`:

```bash
# Diagnosi automatica
python fix_api_key_issue.py

cat .env
```

**Problemi comuni:**
- API key copiata male (spazi, newline)
- API key scaduta o senza crediti
- Confusione tra OpenAI e Azure OpenAI keys

```python
# ✅ SOLUZIONE ROBUSTA
def safe_tree_building(client, text):
    try:
        tree_builder = LLMTreeBuilder(client=client)
        result = tree_builder.build_tree(text)
        
        # Controlla se ha usato fallback
        if result.metadata.get('llm_fallback'):
            print("TreeBuilder fallback - uso TextParser invece")
            return parse_text(text)
        
        return result
    except Exception:
        return parse_text(text)  # Fallback sicuro

# ✅ ANCORA PIÙ SEMPLICE: salta TreeBuilder per iniziare
document = parse_text(text)  # Più affidabile
```

Per esempi dettagliati e configurazioni avanzate, consultare la guida completa.
