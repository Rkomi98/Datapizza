# Guida ai servizi Azure per RAG

Questa guida chiarisce le differenze tra i vari servizi Azure necessari per un sistema RAG completo.

## Servizi Azure coinvolti

### 1. Azure OpenAI (quello che probabilmente hai già)
- **Scopo**: Modelli GPT per chat/completion e embedding
- **Endpoint formato**: `https://your-resource-name.openai.azure.com/`
- **Modelli**: GPT-4, GPT-3.5-turbo, text-embedding-3-small, etc.
- **Uso nel RAG**: Generazione risposte e embedding per similarità

### 2. Azure Document Intelligence (servizio separato)
- **Scopo**: Parsing avanzato di PDF, estrazione layout, tabelle, immagini
- **Endpoint formato**: `https://your-doc-intel-resource.cognitiveservices.azure.com/`  
- **Uso nel RAG**: Parsing strutturato di documenti complessi
- **Note**: È il servizio che richiede `AzureParser` in datapizzai

### 3. Servizi opzionali
- **Azure Storage**: Per salvare documenti/cache
- **Azure Container Instances**: Per hosting Qdrant in cloud

## Soluzioni per il tuo caso

### ✅ Soluzione 1: Solo Azure OpenAI (raccomandato per iniziare)

Usa l'esempio `simple_rag_example.py` che:
- Funziona con quello che hai già (Azure OpenAI)
- Parsing PDF semplice con PyPDF2
- Stessa funzionalità RAG di base

```bash
# Dipendenze necessarie
pip install PyPDF2 python-dotenv

# File di configurazione
cp azure_openai_config.example.env .env
# Modifica .env con le tue credenziali Azure OpenAI

# Avvia Qdrant locale
docker run -p 6333:6333 qdrant/qdrant

# Esegui esempio
python simple_rag_example.py
```

### ⚠️ Soluzione 2: Aggiungere Azure Document Intelligence

Se vuoi parsing avanzato (layout, tabelle, OCR), devi:

1. **Creare Azure Document Intelligence**:
   - Vai su Azure Portal
   - Crea risorsa "Document Intelligence"
   - Ottieni endpoint e key

2. **Configurare**:
   ```bash
   # Nel tuo .env
   AZURE_DOCUMENT_INTELLIGENCE_KEY=your_key
   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
   ```

3. **Modificare codice**:
   ```python
   # Invece di SimpleParser
   from datapizzai.modules.parsers import AzureParser
   
   parser = AzureParser(
       api_key=os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY'),  # Non AZURE_OPENAI_KEY!
       endpoint=os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'),  # Non OPENAI_ENDPOINT!
       result_type="markdown"
   )
   ```

### 🌐 Soluzione 3: OpenAI diretto (alternativa)

Se preferisci OpenAI diretto invece di Azure:

```python
from datapizzai.clients import OpenAIClient

client = OpenAIClient(
    api_key=os.getenv('OPENAI_API_KEY'),  # Direttamente da OpenAI
    model_name="gpt-4"
)
```

## Costi orientativi

### Azure OpenAI
- GPT-4: ~$30-60 per 1M token
- Embedding: ~$0.10 per 1M token
- Text-embedding-3-small: più economico

### Azure Document Intelligence
- ~$1-15 per 1000 pagine (dipende dal tipo di analisi)
- Gratuito: 500 pagine/mese

### OpenAI diretto
- Simile ad Azure OpenAI
- A volte più conveniente per uso sporadico

## Raccomandazione

**Per iniziare subito**: usa `simple_rag_example.py` con Azure OpenAI che hai già.

**Per produzione avanzata**: aggiungi Azure Document Intelligence solo se hai bisogno di:
- Parsing layout complessi
- Estrazione tabelle precise  
- OCR di immagini
- Analisi documenti scansionati

## Troubleshooting comuni

### Errore 404 ResourceNotFound
- **Causa**: Stai usando endpoint sbagliato
- **Fix**: Verifica che usi l'endpoint giusto per il servizio giusto

### Errore di autenticazione
- **Causa**: API key sbagliata o scaduta
- **Fix**: Verifica le credenziali in Azure Portal

### Modello non trovato
- **Causa**: Modello non deployato nella tua risorsa Azure
- **Fix**: Deploya il modello in Azure AI Studio

### Rate limiting
- **Causa**: Troppo traffico
- **Fix**: Implementa retry logic o aumenta quota
