<h1 align="center">
  <img src="https://via.placeholder.com/800x200/FF0000/FFFFFF?text=DatapizzAI" alt="DatapizzAI Banner">
  <br>
  🍕 DatapizzAI Framework
  <br>
</h1>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-red?style=for-the-badge&logo=python&logoColor=white"/>
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>
  <img alt="Version" src="https://img.shields.io/badge/Version-3.0.8+-black?style=for-the-badge"/>
</p>

<p align="center">
  <b>Il framework AI più semplice e potente per costruire sistemi intelligenti in pochi minuti</b>
</p>

<p align="center">
  <img src="https://via.placeholder.com/600x400/000000/00FF00?text=Framework+Demo" alt="Demo GIF">
</p>

---

## 🚀 Indice

1. [Installazione & Setup](#-installazione--setup)
2. [Client Base](#-client-base)
3. [Client Personalizzato](#-client-personalizzato)
4. [Tool Semplice](#-tool-semplice)
5. [Agente AI](#-agente-ai)
6. [Pipeline](#-pipeline)
7. [Sistema RAG](#-sistema-rag)

---

## 📦 Installazione & Setup

**Descrizione breve:** Configura DatapizzAI in 30 secondi e inizia subito a costruire.

### Installazione

```bash
pip install datapizzai
```

### Setup Iniziale

```python
# .env file
OPENAI_API_KEY=sk-your-key-here
```

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory

# Carica le variabili d'ambiente
load_dotenv()

# Crea il tuo primo client in una riga
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

# Test immediato
response = client.invoke("Ciao! Dimmi un fatto interessante sulla pizza 🍕")
print(response.text)
```

**Spiegazione del codice:** Il setup richiede solo tre passaggi: installazione del pacchetto, configurazione della chiave API nel file `.env`, e creazione del client con una singola chiamata a `ClientFactory.create()`. Il framework gestisce automaticamente tutte le configurazioni complesse.

**Risultato atteso:**
```
"La pizza Margherita fu creata nel 1889 per onorare la Regina Margherita di Savoia, 
con pomodoro, mozzarella e basilico che rappresentano i colori della bandiera italiana!"
```

![Setup Animation](https://via.placeholder.com/800x400/FF0000/FFFFFF?text=Setup+in+30+secondi)

---

## 🤖 Client Base

**Descrizione breve:** Interagisci con qualsiasi LLM usando la stessa interfaccia unificata.

### Esempio Multi-Provider

```python
from datapizzai.clients import ClientFactory

# Stesso codice per TUTTI i provider!
providers = {
    "openai": "gpt-4o",
    "google": "gemini-2.0-flash", 
    "anthropic": "claude-3-sonnet"
}

for provider, model in providers.items():
    client = ClientFactory.create(
        provider=provider,
        api_key=os.getenv(f"{provider.upper()}_API_KEY"),
        model=model
    )
    
    response = client.invoke("Scrivi un haiku sulla programmazione")
    print(f"\n{provider.upper()}:\n{response.text}")
```

**Spiegazione del codice:** DatapizzAI astrae le differenze tra i vari provider AI. Con lo stesso identico codice puoi switchare tra OpenAI, Google Gemini, Anthropic Claude e altri, cambiando solo il nome del provider. Non serve imparare API diverse!

**Risultato atteso:**
```
OPENAI:
Codice che scorre
Bug nascosti tra le righe
Debug all'alba

GOOGLE:
Logica pura
Algoritmi che danzano
Compile riuscito
```

### Conversazione con Memoria

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

memory = Memory()
client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")

# Prima domanda
memory.add_turn([TextBlock(content="Mi chiamo Marco")], ROLE.USER)
response = client.invoke("", memory=memory)
memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)

# Seconda domanda - ricorda il contesto!
memory.add_turn([TextBlock(content="Qual è il mio nome?")], ROLE.USER)
response = client.invoke("", memory=memory)
print(response.text)  # "Il tuo nome è Marco!"
```

**Spiegazione del codice:** Il sistema di memoria permette di mantenere il contesto tra le conversazioni. Ogni turno viene salvato con il ruolo appropriato (USER o ASSISTANT), permettendo al modello di ricordare informazioni precedenti senza dover ripetere tutto il contesto.

![Memory Demo](https://via.placeholder.com/800x400/000000/00FF00?text=Conversazione+con+Memoria)

---

## 🔧 Client Personalizzato

**Descrizione breve:** Integra qualsiasi API o modello locale con la stessa interfaccia DatapizzAI.

### Esempio: Ollama Locale

```python
import requests
from datapizzai.type import TextBlock
from datapizzai.clients import ClientResponse

class OllamaClient:
    def __init__(self, model="gemma:2b"):
        self.model = model
        self.base_url = "http://localhost:11434"
    
    def invoke(self, prompt, memory=None):
        # Chiamata API locale
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False}
        )
        
        text = response.json()["response"]
        
        return ClientResponse(
            content=[TextBlock(content=text)],
            prompt_tokens_used=len(prompt.split()),
            completion_tokens_used=len(text.split())
        )

# Usa il client custom come qualsiasi altro!
client = OllamaClient("llama3.2")
response = client.invoke("Spiega la ricorsione in una frase")
print(response.text)
```

**Spiegazione del codice:** Creando una classe che implementa il metodo `invoke()` e restituisce un `ClientResponse`, puoi integrare qualsiasi servizio AI (locale o remoto) nel framework. Questo esempio mostra l'integrazione con Ollama per eseguire modelli completamente offline.

**Risultato atteso:**
```
"La ricorsione è quando una funzione chiama se stessa per risolvere 
un problema dividendolo in sottoproblemi più piccoli."
```

![Custom Client](https://via.placeholder.com/800x400/FF0000/000000?text=Client+Personalizzato)

---

## 🛠️ Tool Semplice

**Descrizione breve:** Dai superpoteri al tuo AI con tool che può chiamare autonomamente.

### Calcolatrice e Meteo

```python
from datapizzai.tools import tool
from datapizzai.clients import ClientFactory

@tool
def calcola(espressione: str) -> str:
    """Esegue calcoli matematici"""
    return str(eval(espressione))

@tool  
def meteo(città: str) -> str:
    """Ottiene il meteo attuale"""
    # Simulazione - in produzione useresti una vera API
    return f"Milano: 22°C, soleggiato ☀️"

client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")

# L'AI decide autonomamente quali tool usare!
response = client.invoke(
    "Quanto fa 127 * 89? E che tempo fa a Milano?",
    tools=[calcola, meteo],
    tool_choice="auto"
)

print(response.text)
```

**Spiegazione del codice:** I tool sono funzioni Python decorate con `@tool` che l'AI può chiamare autonomamente quando necessario. Il decorator gestisce automaticamente la conversione in formato compatibile con l'API. L'AI analizza la domanda e decide quali tool utilizzare per rispondere correttamente.

**Risultato atteso:**
```
"127 moltiplicato per 89 fa 11,303. 
Per quanto riguarda il meteo, a Milano ci sono 22°C con cielo soleggiato ☀️"
```

### Tool con Side Effects

```python
@tool
def invia_email(destinatario: str, oggetto: str, corpo: str) -> str:
    """Invia una email"""
    # Qui chiameresti il vero servizio email
    print(f"📧 Email inviata a {destinatario}")
    return f"Email inviata con successo a {destinatario}"

@tool
def salva_promemoria(testo: str, quando: str) -> str:
    """Salva un promemoria"""
    print(f"📝 Promemoria salvato: {testo} per {quando}")
    return "Promemoria salvato"

response = client.invoke(
    "Invia a marco@example.com un'email per ricordargli la riunione di domani alle 15",
    tools=[invia_email, salva_promemoria]
)
```

![Tools Demo](https://via.placeholder.com/800x400/000000/FF0000?text=AI+con+Superpoteri)

---

## 🤖 Agente AI

**Descrizione breve:** Crea agenti autonomi che ragionano, pianificano e agiscono.

### Agente Singolo

```python
from datapizzai.agents import Agent
from datapizzai.tools import tool

@tool
def cerca_web(query: str) -> str:
    """Cerca informazioni sul web"""
    return f"Risultati per '{query}': DatapizzAI è il framework AI più semplice"

@tool
def analizza_sentimento(testo: str) -> str:
    """Analizza il sentimento di un testo"""
    return "Sentimento: Positivo (95% confidence)"

# Crea un agente specializzato
agent = Agent(
    name="ResearchBot",
    client=client,
    system_prompt="Sei un ricercatore esperto. Analizza sempre fonti e sentimenti.",
    tools=[cerca_web, analizza_sentimento],
    planning_interval=3  # Ripianifica ogni 3 step
)

# L'agente pianifica e esegue autonomamente!
result = agent.run("Cosa pensano gli sviluppatori di DatapizzAI?")
print(result)
```

**Spiegazione del codice:** Un agente è un'entità autonoma che combina un LLM con tool e capacità di pianificazione. L'agente analizza l'obiettivo, crea un piano d'azione, esegue i tool necessari e sintetizza i risultati. Il `planning_interval` permette di ripianificare periodicamente per task complessi.

**Risultato atteso:**
```
"Basandomi sulla ricerca, gli sviluppatori apprezzano molto DatapizzAI 
per la sua semplicità d'uso (sentimento positivo al 95%). 
È considerato il framework AI più intuitivo disponibile."
```

### Sistema Multi-Agente

```python
from datapizzai.agents import Agent

# Agente analista
analyst = Agent(
    name="DataAnalyst",
    client=client,
    system_prompt="Analizza dati e trova pattern"
)

# Agente scrittore  
writer = Agent(
    name="Writer",
    client=client,
    system_prompt="Scrivi report chiari e concisi"
)

# Coordinatore che orchestra gli altri agenti
coordinator = Agent(
    name="Coordinator",
    client=client,
    system_prompt="Coordina il team per completare task complessi",
    can_call=[analyst, writer]  # Può delegare a questi agenti!
)

# Il coordinatore gestisce tutto autonomamente
result = coordinator.run(
    "Analizza i dati di vendita e scrivi un report esecutivo"
)
```

**Spiegazione del codice:** Il sistema multi-agente permette di creare team di AI specializzati. Il coordinatore può delegare task specifici agli agenti appropriati tramite `can_call`. Ogni agente ha competenze specifiche e il coordinatore orchestra il loro lavoro per completare obiettivi complessi.

![Multi-Agent System](https://via.placeholder.com/800x400/00FF00/000000?text=Sistema+Multi-Agente)

---

## 📊 Pipeline

**Descrizione breve:** Costruisci flussi di elaborazione complessi con componenti modulari.

### Pipeline di Analisi Sentiment

```python
from datapizzai.pipeline import DagPipeline
from datapizzai.core.models import PipelineComponent

class LoadReviews(PipelineComponent):
    def _run(self, **kwargs):
        return {"reviews": [
            "Prodotto fantastico, lo consiglio!",
            "Pessima esperienza, da evitare",
            "Nella media, niente di speciale"
        ]}

class AnalyzeSentiment(PipelineComponent):
    def _run(self, reviews, **kwargs):
        sentiments = []
        for review in reviews:
            if "fantastico" in review or "consiglio" in review:
                sentiments.append({"text": review, "sentiment": "positivo"})
            elif "pessim" in review or "evitare" in review:
                sentiments.append({"text": review, "sentiment": "negativo"})
            else:
                sentiments.append({"text": review, "sentiment": "neutro"})
        return {"results": sentiments}

class GenerateReport(PipelineComponent):
    def _run(self, results, **kwargs):
        pos = sum(1 for r in results if r["sentiment"] == "positivo")
        neg = sum(1 for r in results if r["sentiment"] == "negativo")
        return {"report": f"📊 Positivi: {pos}, Negativi: {neg}, Neutri: {len(results)-pos-neg}"}

# Costruisci la pipeline
pipeline = DagPipeline()
pipeline.add_module("loader", LoadReviews())
pipeline.add_module("analyzer", AnalyzeSentiment())
pipeline.add_module("reporter", GenerateReport())

# Connetti i componenti
pipeline.connect("loader", "analyzer", "reviews", "reviews")
pipeline.connect("analyzer", "reporter", "results", "results")

# Esegui!
result = pipeline.run({})
print(result["reporter"]["report"])
```

**Spiegazione del codice:** Le pipeline permettono di creare flussi di elaborazione modulari e riutilizzabili. Ogni componente è indipendente e può essere testato separatamente. La DagPipeline gestisce automaticamente le dipendenze e l'ordine di esecuzione, permettendo anche elaborazione parallela dove possibile.

**Risultato atteso:**
```
"📊 Positivi: 1, Negativi: 1, Neutri: 1"
```

### Pipeline con Branching

```python
from datapizzai.pipeline import FunctionalPipeline

pipeline = (
    FunctionalPipeline()
    .run(name="load", node=LoadReviews())
    .then(name="analyze", node=AnalyzeSentiment(), target_key="reviews")
    .branch(
        condition=lambda ctx: len(ctx.get("analyze", {}).get("results", [])) > 10,
        if_true=DetailedAnalysisPipeline(),
        if_false=QuickSummaryPipeline()
    )
)

result = pipeline.execute()
```

![Pipeline Flow](https://via.placeholder.com/800x400/FF0000/00FF00?text=Pipeline+Modulare)

---

## 📚 Sistema RAG

**Descrizione breve:** Costruisci un sistema completo di Retrieval-Augmented Generation in pochi minuti.

### Setup Veloce RAG

```python
from datapizzai.modules.parsers import TextParser
from datapizzai.modules.splitters import TextSplitter
from datapizzai.embedders import NodeEmbedder
from datapizzai.vectorstores import QdrantVectorstore
from qdrant_client import QdrantClient

# 1. Prepara il documento
text = """
DatapizzAI è un framework rivoluzionario per l'AI.
Permette di costruire sistemi intelligenti rapidamente.
La sua semplicità lo rende accessibile a tutti gli sviluppatori.
"""

# 2. Parse e split del documento
parser = TextParser()
document = parser.parse(text)

splitter = TextSplitter(max_char=100, overlap=20)
chunks = splitter(document)

# 3. Genera embeddings
embedder = NodeEmbedder(
    client=client,
    model_name="text-embedding-3-small"
)
embedded_chunks = embedder(chunks)

# 4. Salva nel vector store
vectorstore = QdrantVectorstore(host="localhost", port=6333)
vectorstore.add(embedded_chunks, collection_name="docs")

# 5. Query e retrieval
query = "Cos'è DatapizzAI?"
query_embedding = client.embed(query)

results = vectorstore.search(
    query_vector=query_embedding,
    collection_name="docs",
    limit=3
)

# 6. Genera risposta con contesto
context = "\n".join([r.text for r in results])
response = client.invoke(f"Contesto: {context}\n\nDomanda: {query}")
print(response.text)
```

**Spiegazione del codice:** Il sistema RAG combina retrieval e generazione. Prima i documenti vengono parsati, divisi in chunk e convertiti in embeddings. Questi vengono salvati in un vector database. Quando arriva una query, si cercano i chunk più rilevanti e si usano come contesto per generare una risposta accurata basata sui documenti.

**Risultato atteso:**
```
"DatapizzAI è un framework rivoluzionario per l'intelligenza artificiale 
che permette agli sviluppatori di costruire sistemi intelligenti in modo 
rapido e semplice, rendendolo accessibile a tutti."
```

### RAG Avanzato con Reranking

```python
from datapizzai.modules.rerankers import CohereReranker
from datapizzai.modules.metatagger import KeywordMetatagger

# Aggiungi metadati ai chunks
metatagger = KeywordMetatagger(client=client)
tagged_chunks = metatagger(chunks)

# Reranking per migliorare la relevanza
reranker = CohereReranker(
    api_key=os.getenv("COHERE_API_KEY"),
    top_n=3
)

# Pipeline completa RAG
def advanced_rag_query(question):
    # 1. Embed query
    query_vec = client.embed(question)
    
    # 2. Retrieval iniziale
    candidates = vectorstore.search(query_vec, limit=10)
    
    # 3. Reranking
    reranked = reranker.run({
        "query": question,
        "documents": candidates
    })
    
    # 4. Genera risposta finale
    context = "\n".join([d.text for d in reranked])
    return client.invoke(f"Contesto: {context}\nDomanda: {question}")

response = advanced_rag_query("Come posso iniziare con DatapizzAI?")
```

![RAG System](https://via.placeholder.com/800x400/000000/FF0000?text=Sistema+RAG+Completo)

---

## 🎯 Prossimi Passi

Ora che hai visto la potenza e semplicità di DatapizzAI, ecco come continuare:

1. **Esplora gli esempi completi** nella cartella `/examples`
2. **Unisciti alla community** su Discord per supporto e idee
3. **Contribuisci** al progetto su GitHub

<p align="center">
  <img src="https://via.placeholder.com/600x200/FF0000/FFFFFF?text=Inizia+a+Costruire+Oggi!" alt="CTA">
</p>

<p align="center">
  <b>🍕 DatapizzAI - L'AI semplice come ordinare una pizza!</b>
</p>

---

<p align="center">
  Made with ❤️ by the DataPizza Team
</p>