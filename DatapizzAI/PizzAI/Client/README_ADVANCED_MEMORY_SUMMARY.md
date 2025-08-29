# Gestione avanzata del summary della memoria

Esempio avanzato per la gestione intelligente del summary della memoria con DatapizzAI. Questo esempio estende significativamente le funzionalità base mostrando tecniche professionali per applicazioni di produzione.

## Indice

- Differenze con l'esempio base
- Strategie di summarization disponibili
- Configurazione
- Configurazioni per scenari specifici
- Utilizzo base
- Cache Redis per produzione
- Monitoraggio e debug
- Gestione errori e recovery
- Best practices per produzione
- Confronto prestazioni
- Limitazioni e sviluppi futuri
- Demo ed esempi

## Differenze con l'esempio base

L'esempio nel README principale `SummarizingChat` è volutamente semplice per fini didattici. Questo esempio avanzato aggiunge:

- **Strategie multiple** di summarization (non solo riassunto completo)
- **Persistenza** automatica su file con backup
- **Cache intelligente** per i summary generati 
- **Metriche dettagliate** per monitoraggio e debug
- **Gestione robusta degli errori** con fallback
- **Configurazione flessibile** per diversi scenari
- **Logging professionale** per debugging
- **Auto-save** periodico della memoria
- **Analisi della memoria** prima delle decisioni

## Strategie di summarization disponibili

### 1. Full summary (FULL_SUMMARY)
Riassunto completo di tutta la memoria, poi reset.
- **Uso**: quando la memoria diventa troppo lunga
- **Pro**: massima riduzione di token
- **Contro**: perdita del contesto conversazionale

### 2. Keep recent (KEEP_RECENT) 
Riassume tutto tranne gli ultimi N messaggi.
- **Uso**: mantiene il flusso conversazionale recente
- **Pro**: bilancia riduzione token e contesto
- **Contro**: messaggi antichi importanti potrebbero perdersi

### 3. Importance based (IMPORTANCE_BASED)
Mantiene messaggi con parole chiave importanti.
- **Uso**: conversazioni tecniche o di business
- **Pro**: preserva informazioni critiche
- **Contro**: richiede configurazione delle keywords

### 4. Hierarchical (HIERARCHICAL) - *Da implementare*  
Summary gerarchico (riassunto di riassunti).

## Configurazione

```python
from advanced_memory_summary import SummaryConfig, SummaryStrategy

# Configurazione per applicazioni di produzione
config = SummaryConfig(
    strategy=SummaryStrategy.KEEP_RECENT,
    trigger_turns=10,                     # Dopo 10 turni
    trigger_tokens=6000,                  # O 6000 token stimati
    keep_recent_turns=3,                  # Mantieni 3 turni recenti
    summary_max_tokens=300,               # Summary fino a 300 token
    importance_keywords=[                 # Keywords personalizzate
        'importante', 'decisione', 'todo', 'problema', 
        'budget', 'deadline', 'requisito', 'specifiche'
    ],
    auto_save_interval=5,                 # Save ogni 5 turni
    cache_summaries=True                  # Cache abilitata
)
```

### Configurazioni per scenari specifici

#### Assistente tecnico
```python
config = SummaryConfig(
    strategy=SummaryStrategy.IMPORTANCE_BASED,
    trigger_turns=15,
    trigger_tokens=8000,
    importance_keywords=[
        'errore', 'bug', 'fix', 'implementazione', 
        'api', 'database', 'sicurezza', 'performance'
    ]
)
```

#### Chatbot customer service
```python
config = SummaryConfig(
    strategy=SummaryStrategy.KEEP_RECENT,
    trigger_turns=8,
    trigger_tokens=4000,
    keep_recent_turns=4,  # Mantieni più contesto
    importance_keywords=[
        'reclamo', 'problema', 'urgente', 'risolvere',
        'cliente', 'ordine', 'pagamento', 'spedizione'
    ]
)
```

#### Brainstorming creativo
```python
config = SummaryConfig(
    strategy=SummaryStrategy.FULL_SUMMARY,  # Riassunto creativo
    trigger_turns=12,
    trigger_tokens=7000,
    summary_max_tokens=400,  # Summary più lungo per creatività
)
```

## Utilizzo base

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.cache import MemoryCache
from advanced_memory_summary import AdvancedMemoryManager, SummaryConfig, SummaryStrategy

load_dotenv()

# Client con cache
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.7,
    cache=MemoryCache()
)

# Configurazione
config = SummaryConfig(
    strategy=SummaryStrategy.KEEP_RECENT,
    trigger_turns=8,
    trigger_tokens=5000,
    keep_recent_turns=3
)

# Manager con persistenza
manager = AdvancedMemoryManager(
    client=client,
    config=config,
    memory_file="conversation_memory.json",
    cache_type="memory"  # o "redis" per ambienti distribuiti
)

# Conversazione
while True:
    user_input = input("Tu> ").strip()
    if user_input.lower() in ['exit', 'esci', 'quit']:
        break
        
    try:
        response = manager.send_message(user_input)
        print(f"Bot> {response}")
        
        # Mostra statistiche occasionalmente
        if len(manager.memory) % 5 == 0:
            stats = manager.get_memory_stats()
            print(f"[INFO] {stats['current_metrics']['total_turns']} turni, "
                  f"~{stats['current_metrics']['estimated_tokens']} token")
            
    except Exception as e:
        print(f"Errore: {e}")
```

## Cache Redis per produzione

Per applicazioni distribuite, usa Redis come cache condivisa:

```python
from datapizzai.cache import RedisCache

# Redis cache
redis_cache = RedisCache(
    host="localhost", 
    port=6379, 
    db=0,
    expiration_time=7200  # 2 ore
)

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    cache=redis_cache
)

manager = AdvancedMemoryManager(
    client=client,
    config=config,
    memory_file="memory.json",
    cache_type="redis"  # Cache Redis anche per i summary
)
```

## Monitoraggio e debug

### Metriche disponibili
```python
stats = manager.get_memory_stats()

print("Metriche correnti:")
print(f"- Turni: {stats['current_metrics']['total_turns']}")  
print(f"- Token stimati: {stats['current_metrics']['estimated_tokens']}")
print(f"- Età memoria: {stats['current_metrics']['oldest_turn_age']:.1f}s")
print(f"- Summary generati: {stats['summary_history_count']}")
print(f"- Strategia: {stats['current_strategy']}")
print(f"- Cache attiva: {stats['cache_enabled']}")
```

### Cronologia summary
```python
# Accedi alla cronologia completa
for summary_entry in manager.summary_history:
    print(f"Data: {summary_entry['timestamp']}")
    print(f"Strategia: {summary_entry['strategy']}")
    print(f"Tempo: {summary_entry['elapsed_time']:.2f}s")
    print(f"Summary: {summary_entry['summary'][:100]}...")
    print(f"Riduzione token: {summary_entry['metrics_before']['estimated_tokens']} → {summary_entry['metrics_after']['estimated_tokens']}")
    print()
```

### Logging per debug
```python
import logging

# Configura logging dettagliato
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memory_manager.log'),
        logging.StreamHandler()
    ]
)

# Ora vedrai log dettagliati di:
# - Trigger dei summary
# - Cache hit/miss
# - Metriche prima/dopo
# - Errori e fallback
```

## Gestione errori e recovery

Il manager gestisce automaticamente:

- **Errori di API**: fallback senza perdere la memoria
- **Problemi di cache**: continua senza cache
- **File corrotti**: crea backup automatici
- **Summary falliti**: mantiene memoria originale

```python
# Backup manuale prima di operazioni rischiose
backup_memory = manager.memory.copy()

try:
    # Operazione potenzialmente pericolosa
    risky_operation()
except Exception as e:
    # Ripristino automatico
    manager.memory = backup_memory
    logger.error(f"Ripristinato backup dopo errore: {e}")

# Reset completo se necessario (richiede conferma)
success = manager.reset_memory(confirm=True)
```

## Best practices per produzione

### 1. Configurazione del trigger
```python
# Per conversazioni brevi (< 20 messaggi)
config = SummaryConfig(trigger_turns=12, trigger_tokens=4000)

# Per conversazioni lunghe (sessioni di lavoro)  
config = SummaryConfig(trigger_turns=25, trigger_tokens=10000)

# Per applicazioni con vincoli di token strict
config = SummaryConfig(trigger_turns=6, trigger_tokens=2000)
```

### 2. Scelta della strategia
- **Customer service**: `KEEP_RECENT` (mantiene contesto immediato)
- **Consulenza tecnica**: `IMPORTANCE_BASED` (preserva info tecniche)
- **Chatbot generico**: `FULL_SUMMARY` (massima efficienza)

### 3. Monitoring in produzione
```python
# Metriche periodiche per monitoraggio
def log_metrics_periodically(manager):
    stats = manager.get_memory_stats()
    
    # Log per sistemi di monitoring
    logger.info("METRICS", extra={
        'turns': stats['current_metrics']['total_turns'],
        'tokens': stats['current_metrics']['estimated_tokens'], 
        'summaries': stats['summary_history_count'],
        'strategy': stats['current_strategy']
    })
```

### 4. Gestione della persistenza
```python
# File diversi per utente/sessione
memory_file = f"memory_{user_id}_{session_id}.json"
manager = AdvancedMemoryManager(
    client=client,
    config=config, 
    memory_file=memory_file
)

# Cleanup periodico dei file vecchi
cleanup_old_memory_files(days_old=30)
```

## Confronto prestazioni

| Funzionalità | Esempio base | Esempio avanzato |
|--------------|--------------|------------------|
| Strategie | 1 (riassunto completo) | 3+ (configurabili) |
| Persistenza | ❌ | ✅ Automatica con backup |
| Cache | ❌ | ✅ Memory/Redis |
| Metriche | ❌ | ✅ Dettagliate |
| Error handling | ❌ | ✅ Robusto |
| Logging | ❌ | ✅ Professionale |
| Configurazione | Hard-coded | ✅ Flessibile |
| Recovery | ❌ | ✅ Backup automatici |

## Limitazioni e sviluppi futuri

### Limitazioni correnti
- Strategia `HIERARCHICAL` non ancora implementata
- Cache Redis richiede server Redis separato
- Stima token approssimativa (chars/4), non precisa come tiktoken

### Roadmap
- [ ] Summary gerarchico per conversazioni molto lunghe
- [ ] Integrazione tiktoken per conteggio preciso
- [ ] Compressione automatica dei file memoria
- [ ] Dashboard web per monitoring
- [ ] Plugin per diversi LLM provider

## Demo ed esempi

Esegui la demo completa:
```bash
cd Client/
python advanced_memory_summary.py
```

La demo simula una conversazione di progettazione e-commerce mostrando:
- Trigger automatico del summary
- Riduzione dei token
- Persistenza della memoria
- Uso della cache
- Metriche in tempo reale

---

**Note**: per la documentazione rispetta i principi [[memory:6554780]] e [[memory:6599825]] mantenendo un tono tecnico e professionale con esempi pratici e informazioni accurate.
