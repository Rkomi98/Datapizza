# Gestione avanzata del summary della memoria

Esempio avanzato per la gestione intelligente del summary della memoria con Datapizza-AI. Questo esempio estende significativamente le funzionalità base mostrando tecniche professionali per applicazioni di produzione.

## Indice

- [Differenze con l'esempio base](#differenze-con-lesempio-base)
- [Strategie di summarization disponibili](#strategie-di-summarization-disponibili)
- [Configurazione](#configurazione)
- [Configurazioni per scenari specifici](#configurazioni-per-scenari-specifici)
- [Utilizzo base](#utilizzo-base)
- [Cache Redis per produzione](#cache-redis-per-produzione)
- [Monitoraggio e debug](#monitoraggio-e-debug)
- [Gestione errori e recovery](#gestione-errori-e-recovery)
- [Best practices per produzione](#best-practices-per-produzione)
- [Confronto prestazioni](#confronto-prestazioni)
- [Limitazioni e sviluppi futuri](#limitazioni-e-sviluppi-futuri)
- [Demo ed esempi](#demo-ed-esempi)

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
from advanced_memory_summary import AdvancedMemoryManager, SummaryConfig, SummaryStrategy

load_dotenv()

from datapizza.clients.openai import OpenAIClient

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.7,
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

## Confronto prestazioni

| Funzionalità   |       Esempio base     |      Esempio avanzato    |
|----------------|------------------------|--------------------------|
| Strategie      | 1 (riassunto completo) | 3+ (configurabili)       |
| Persistenza    |            ❌          | ✅ Automatica con backup |
| Cache          |            ❌          | ✅ Memory/Redis          |
| Metriche       |            ❌          | ✅ Dettagliate           |
| Error handling |            ❌          | ✅ Robusto               |
| Logging        |            ❌          | ✅ Professionale         |
| Configurazione |         Hard-coded     | ✅ Flessibile            |
| Recovery       |            ❌          | ✅ Backup automatici     |