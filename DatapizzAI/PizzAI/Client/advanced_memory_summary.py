#!/usr/bin/env python3
"""
Esempio avanzato per la gestione del summary della memoria con DatapizzAI.

Questo esempio mostra tecniche avanzate per:
- Gestione intelligente del summary della memoria 
- Strategie multiple di summarization
- Persistenza e caricamento della memoria
- Analisi delle metriche e delle performance
- Cache per i summary generati
- Gestione robusta degli errori
- Configurazione flessibile

Autore: DatapizzAI Team
"""

import os
import json
import time
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from enum import Enum

from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE
from datapizzai.cache import MemoryCache, RedisCache

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carica variabili d'ambiente
load_dotenv()


class SummaryStrategy(Enum):
    """Strategie disponibili per il summary."""
    FULL_SUMMARY = "full_summary"           # Riassunto completo di tutto
    KEEP_RECENT = "keep_recent"             # Mantiene N messaggi recenti + summary del resto
    IMPORTANCE_BASED = "importance_based"   # Mantiene messaggi "importanti"
    SLIDING_WINDOW = "sliding_window"       # Finestra scorrevole con overlap
    HIERARCHICAL = "hierarchical"           # Summary gerarchico (summary di summary)


@dataclass
class MemoryMetrics:
    """Metriche della memoria per analisi e decisioni."""
    total_turns: int
    total_characters: int
    estimated_tokens: int  # Stima approssimativa (chars / 4)
    oldest_turn_age: float  # Secondi dal primo turn
    memory_hash: int
    last_summary_turns_ago: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_turns': self.total_turns,
            'total_characters': self.total_characters,
            'estimated_tokens': self.estimated_tokens,
            'oldest_turn_age': self.oldest_turn_age,
            'memory_hash': hex(self.memory_hash),
            'last_summary_turns_ago': self.last_summary_turns_ago
        }


@dataclass 
class SummaryConfig:
    """Configurazione per la gestione del summary."""
    strategy: SummaryStrategy = SummaryStrategy.KEEP_RECENT
    trigger_turns: int = 8                    # Dopo quanti turni fare summary
    trigger_tokens: int = 4000                # Limite di token per triggerare summary
    keep_recent_turns: int = 3                # Quanti turni recenti mantenere
    summary_max_tokens: int = 200             # Lunghezza massima del summary
    importance_keywords: List[str] = None     # Parole chiave per messaggi importanti
    auto_save_interval: int = 5               # Auto-save ogni N turni
    cache_summaries: bool = True              # Usa cache per i summary
    
    def __post_init__(self):
        if self.importance_keywords is None:
            self.importance_keywords = [
                'importante', 'decisione', 'todo', 'problema', 'errore',
                'importante', 'critico', 'urgent', 'deadline', 'requisito'
            ]


class AdvancedMemoryManager:
    """
    Gestione avanzata della memoria con strategie multiple di summarization.
    """
    
    def __init__(
        self, 
        client, 
        config: SummaryConfig = None,
        memory_file: str = None,
        cache_type: str = "memory"  # "memory" o "redis"
    ):
        self.client = client
        self.config = config or SummaryConfig()
        self.memory = Memory()
        self.memory_file = Path(memory_file) if memory_file else None
        self.turn_timestamps = []  # Traccia timestamp di ogni turn
        self.summary_history = []  # Storia dei summary generati
        self.turns_since_last_summary = 0
        
        # Setup cache per i summary
        if self.config.cache_summaries:
            if cache_type == "redis":
                try:
                    self.cache = RedisCache()
                    logger.info("Usando RedisCache per i summary")
                except Exception as e:
                    logger.warning(f"Redis non disponibile, fallback a MemoryCache: {e}")
                    self.cache = MemoryCache()
            else:
                self.cache = MemoryCache()
        else:
            self.cache = None
            
        # Carica memoria esistente se disponibile
        self.load_memory()
    
    def get_memory_metrics(self) -> MemoryMetrics:
        """Calcola metriche dettagliate della memoria corrente."""
        total_chars = 0
        total_turns = len(self.memory)
        
        for turn in self.memory:
            for block in turn.blocks:
                if hasattr(block, 'content'):
                    total_chars += len(str(block.content))
        
        # Calcola età del primo turn
        oldest_age = 0.0
        if self.turn_timestamps:
            oldest_age = time.time() - self.turn_timestamps[0]
            
        return MemoryMetrics(
            total_turns=total_turns,
            total_characters=total_chars,
            estimated_tokens=total_chars // 4,  # Stima approssimativa
            oldest_turn_age=oldest_age,
            memory_hash=hash(self.memory),
            last_summary_turns_ago=self.turns_since_last_summary
        )
    
    def should_trigger_summary(self) -> tuple[bool, str]:
        """
        Determina se è necessario fare un summary della memoria.
        
        Returns:
            (should_trigger, reason)
        """
        metrics = self.get_memory_metrics()
        
        # Controllo numero di turni
        if metrics.total_turns >= self.config.trigger_turns:
            return True, f"Raggiunti {metrics.total_turns} turni (limite: {self.config.trigger_turns})"
            
        # Controllo numero di token stimati
        if metrics.estimated_tokens >= self.config.trigger_tokens:
            return True, f"Stimati {metrics.estimated_tokens} token (limite: {self.config.trigger_tokens})"
            
        return False, "Nessun trigger raggiunto"
    
    def _extract_important_turns(self) -> List[int]:
        """Identifica turn contenenti informazioni 'importanti'."""
        important_indices = []
        
        for i, turn in enumerate(self.memory):
            for block in turn.blocks:
                if hasattr(block, 'content'):
                    content = str(block.content).lower()
                    if any(keyword in content for keyword in self.config.importance_keywords):
                        important_indices.append(i)
                        break
                        
        return important_indices
    
    def _generate_summary_prompt(self, turns_to_summarize: List[int]) -> str:
        """Genera il prompt per il summary dei turn specificati."""
        context_parts = []
        
        for turn_idx in turns_to_summarize:
            turn = self.memory[turn_idx]
            role_str = "Utente" if turn.role == ROLE.USER else "Assistente"
            
            for block in turn.blocks:
                if hasattr(block, 'content'):
                    content = str(block.content)[:500]  # Limita lunghezza
                    context_parts.append(f"{role_str}: {content}")
        
        context = "\n".join(context_parts)
        
        prompt = f"""
Riassumi la seguente conversazione in modo conciso e utile.
Mantieni le informazioni chiave, decisioni prese, TODO e problemi identificati.
Limita il riassunto a circa {self.config.summary_max_tokens} token.

CONVERSAZIONE:
{context}

RIASSUNTO:"""
        
        return prompt
    
    def _get_cached_summary(self, content_hash: str) -> Optional[str]:
        """Recupera summary dalla cache se disponibile."""
        if not self.cache:
            return None
            
        try:
            cached = self.cache.get(f"summary_{content_hash}")
            if cached:
                logger.info(f"Summary trovato in cache: {content_hash[:8]}...")
                return cached
        except Exception as e:
            logger.warning(f"Errore accesso cache: {e}")
            
        return None
    
    def _cache_summary(self, content_hash: str, summary: str):
        """Salva summary in cache."""
        if not self.cache:
            return
            
        try:
            self.cache.set(f"summary_{content_hash}", summary)
            logger.info(f"Summary salvato in cache: {content_hash[:8]}...")
        except Exception as e:
            logger.warning(f"Errore salvataggio cache: {e}")
    
    def _apply_strategy_full_summary(self) -> str:
        """Strategia: riassunto completo di tutta la memoria."""
        logger.info("Applicando strategia FULL_SUMMARY")
        
        # Crea hash del contenuto per cache
        content_hash = str(hash(self.memory))
        cached = self._get_cached_summary(content_hash)
        if cached:
            return cached
        
        # Genera summary di tutto
        all_turns = list(range(len(self.memory)))
        prompt = self._generate_summary_prompt(all_turns)
        
        try:
            response = self.client.invoke(prompt)
            summary = response.text.strip()
            
            self._cache_summary(content_hash, summary)
            
            # Reset memoria con solo il summary
            new_memory = Memory()
            new_memory.add_turn([TextBlock(content=f"[RIASSUNTO COMPLETO] {summary}")], ROLE.ASSISTANT)
            
            return summary
            
        except Exception as e:
            logger.error(f"Errore generazione summary completo: {e}")
            return f"[ERRORE SUMMARY] Impossibile generare riassunto: {str(e)}"
    
    def _apply_strategy_keep_recent(self) -> str:
        """Strategia: mantieni N turn recenti + summary del resto."""
        logger.info(f"Applicando strategia KEEP_RECENT (mantieni {self.config.keep_recent_turns} recenti)")
        
        if len(self.memory) <= self.config.keep_recent_turns:
            logger.info("Memoria troppo corta per summary, skip")
            return ""
        
        # Turn da riassumere (tutto tranne gli ultimi N)
        turns_to_summarize = list(range(len(self.memory) - self.config.keep_recent_turns))
        
        # Genera hash per cache
        content_for_hash = "".join([str(hash(self.memory[i])) for i in turns_to_summarize])
        content_hash = str(hash(content_for_hash))
        
        cached = self._get_cached_summary(content_hash)
        if cached:
            summary = cached
        else:
            # Genera nuovo summary
            prompt = self._generate_summary_prompt(turns_to_summarize)
            
            try:
                response = self.client.invoke(prompt)
                summary = response.text.strip()
                self._cache_summary(content_hash, summary)
            except Exception as e:
                logger.error(f"Errore generazione summary: {e}")
                summary = f"[ERRORE] Impossibile riassumere: {str(e)}"
        
        # Ricostruisce memoria: summary + turn recenti
        new_memory = Memory()
        new_memory.add_turn([TextBlock(content=f"[RIASSUNTO PRECEDENTE] {summary}")], ROLE.ASSISTANT)
        
        # Aggiungi turn recenti
        for i in range(len(self.memory) - self.config.keep_recent_turns, len(self.memory)):
            turn = self.memory[i]
            new_memory.add_turn(turn.blocks.copy(), turn.role)
        
        return summary
    
    def _apply_strategy_importance_based(self) -> str:
        """Strategia: mantieni messaggi importanti + summary del resto."""
        logger.info("Applicando strategia IMPORTANCE_BASED")
        
        important_turns = self._extract_important_turns()
        logger.info(f"Trovati {len(important_turns)} turn importanti: {important_turns}")
        
        # Turn da riassumere (quelli non importanti)
        all_turns = set(range(len(self.memory)))
        important_set = set(important_turns)
        turns_to_summarize = list(all_turns - important_set)
        
        if not turns_to_summarize:
            logger.info("Tutti i turn sono importanti, nessun summary necessario")
            return ""
        
        # Genera summary dei turn non importanti
        content_hash = str(hash("".join([str(hash(self.memory[i])) for i in turns_to_summarize])))
        cached = self._get_cached_summary(content_hash)
        
        if cached:
            summary = cached
        else:
            prompt = self._generate_summary_prompt(turns_to_summarize)
            try:
                response = self.client.invoke(prompt)
                summary = response.text.strip()
                self._cache_summary(content_hash, summary)
            except Exception as e:
                logger.error(f"Errore summary: {e}")
                summary = f"[ERRORE] {str(e)}"
        
        # Ricostruisce memoria: summary + turn importanti
        new_memory = Memory()
        new_memory.add_turn([TextBlock(content=f"[RIASSUNTO GENERALE] {summary}")], ROLE.ASSISTANT)
        
        # Aggiungi turn importanti in ordine cronologico
        for turn_idx in sorted(important_turns):
            turn = self.memory[turn_idx]
            new_memory.add_turn(turn.blocks.copy(), turn.role)
        
        return summary
    
    def apply_summary_strategy(self) -> Optional[str]:
        """
        Applica la strategia di summary configurata.
        
        Returns:
            Il testo del summary generato, o None se non applicato
        """
        should_trigger, reason = self.should_trigger_summary()
        if not should_trigger:
            logger.debug(f"Summary non necessario: {reason}")
            return None
        
        logger.info(f"Triggering summary: {reason}")
        metrics_before = self.get_memory_metrics()
        
        start_time = time.time()
        summary = ""
        
        try:
            # Backup della memoria originale
            original_memory = self.memory.copy()
            
            # Applica strategia
            if self.config.strategy == SummaryStrategy.FULL_SUMMARY:
                summary = self._apply_strategy_full_summary()
                # Reset completo
                self.memory.clear()
                self.memory.add_turn([TextBlock(content=f"[RIASSUNTO] {summary}")], ROLE.ASSISTANT)
                
            elif self.config.strategy == SummaryStrategy.KEEP_RECENT:
                summary = self._apply_strategy_keep_recent()
                # La memoria è già stata ricostruita nella strategia
                
            elif self.config.strategy == SummaryStrategy.IMPORTANCE_BASED:
                summary = self._apply_strategy_importance_based()
                # La memoria è già stata ricostruita nella strategia
                
            else:
                logger.warning(f"Strategia {self.config.strategy} non ancora implementata")
                return None
            
            # Aggiorna timestamp e contatori
            self.turn_timestamps = self.turn_timestamps[-len(self.memory):]  # Mantieni solo quelli validi
            self.turns_since_last_summary = 0
            
            # Calcola metriche dopo
            metrics_after = self.get_memory_metrics()
            elapsed_time = time.time() - start_time
            
            # Log riassunto delle operazioni
            logger.info(f"""
    Summary completato in {elapsed_time:.2f}s
    Strategia: {self.config.strategy.value}
    Turn: {metrics_before.total_turns} → {metrics_after.total_turns}
    Token stimati: {metrics_before.estimated_tokens} → {metrics_after.estimated_tokens}
    Riduzione: {((metrics_before.estimated_tokens - metrics_after.estimated_tokens) / metrics_before.estimated_tokens * 100):.1f}%
            """.strip())
            
            # Salva in cronologia
            self.summary_history.append({
                'timestamp': datetime.now().isoformat(),
                'strategy': self.config.strategy.value,
                'summary': summary,
                'metrics_before': metrics_before.to_dict(),
                'metrics_after': metrics_after.to_dict(),
                'elapsed_time': elapsed_time
            })
            
            # Auto-save se configurato
            self.save_memory()
            
            return summary
            
        except Exception as e:
            logger.error(f"Errore durante summary: {e}")
            # Ripristina memoria originale in caso di errore
            self.memory = original_memory
            return None
    
    def send_message(self, user_input: str) -> str:
        """
        Invia un messaggio e gestisce automaticamente il summary se necessario.
        """
        # Aggiungi timestamp per questo turn
        self.turn_timestamps.append(time.time())
        
        # Aggiungi messaggio utente
        self.memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        # Verifica se serve summary PRIMA di chiamare il modello
        self.apply_summary_strategy()
        
        try:
            # Chiama il modello
            response = self.client.invoke("", memory=self.memory)
            
            # Aggiungi risposta alla memoria
            self.memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
            # Aggiorna contatori
            self.turns_since_last_summary += 2  # User + Assistant turn
            
            # Auto-save periodico
            if len(self.memory) % self.config.auto_save_interval == 0:
                self.save_memory()
            
            # Log metriche periodicamente
            if len(self.memory) % 10 == 0:
                metrics = self.get_memory_metrics()
                logger.info(f"Memoria: {metrics.total_turns} turn, ~{metrics.estimated_tokens} token")
            
            return response.text
            
        except Exception as e:
            logger.error(f"Errore durante invocazione: {e}")
            # Rimuovi l'ultimo messaggio utente se fallisce
            if self.memory and self.memory[-1].role == ROLE.USER:
                del self.memory[-1]
                self.turn_timestamps.pop()
            raise
    
    def save_memory(self):
        """Salva memoria e cronologia su file."""
        if not self.memory_file:
            return
            
        try:
            data = {
                'memory': self.memory.to_dict(),
                'turn_timestamps': self.turn_timestamps,
                'summary_history': self.summary_history,
                'turns_since_last_summary': self.turns_since_last_summary,
                'config': {
                    'strategy': self.config.strategy.value,
                    'trigger_turns': self.config.trigger_turns,
                    'trigger_tokens': self.config.trigger_tokens,
                    'keep_recent_turns': self.config.keep_recent_turns,
                    'summary_max_tokens': self.config.summary_max_tokens,
                    'importance_keywords': self.config.importance_keywords,
                }
            }
            
            # Backup del file esistente
            if self.memory_file.exists():
                backup_file = self.memory_file.with_suffix('.backup')
                self.memory_file.rename(backup_file)
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Memoria salvata: {self.memory_file}")
            
        except Exception as e:
            logger.error(f"Errore salvataggio memoria: {e}")
    
    def load_memory(self):
        """Carica memoria da file se esiste."""
        if not self.memory_file or not self.memory_file.exists():
            return
            
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Carica memoria
            if 'memory' in data:
                self.memory.clear()
                for turn_data in data['memory']:
                    from datapizzai.type import Block
                    blocks = [Block.from_dict(block_data) for block_data in turn_data['blocks']]
                    self.memory.add_turn(blocks, ROLE(turn_data['role']))
            
            # Carica altri dati
            self.turn_timestamps = data.get('turn_timestamps', [])
            self.summary_history = data.get('summary_history', [])
            self.turns_since_last_summary = data.get('turns_since_last_summary', 0)
            
            logger.info(f"Memoria caricata: {len(self.memory)} turn, {len(self.summary_history)} summary storici")
            
        except Exception as e:
            logger.error(f"Errore caricamento memoria: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche dettagliate sulla memoria."""
        metrics = self.get_memory_metrics()
        
        return {
            'current_metrics': metrics.to_dict(),
            'summary_history_count': len(self.summary_history),
            'current_strategy': self.config.strategy.value,
            'cache_enabled': self.cache is not None,
            'auto_save_enabled': self.memory_file is not None,
            'last_summary': self.summary_history[-1] if self.summary_history else None
        }
    
    def reset_memory(self, confirm: bool = False):
        """Reset completo della memoria (richiede conferma)."""
        if not confirm:
            logger.warning("Reset memoria richiede conferma esplicita")
            return False
            
        self.memory.clear()
        self.turn_timestamps.clear()
        self.summary_history.clear()
        self.turns_since_last_summary = 0
        
        # Cancella anche il file
        if self.memory_file and self.memory_file.exists():
            self.memory_file.unlink()
            
        logger.info("Memoria resettata completamente")
        return True


def demo_advanced_memory():
    """Dimostra l'utilizzo dell'Advanced Memory Manager."""
    
    print("=== Demo Advanced Memory Management ===\n")
    
    # Configurazione
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",  # Modello più economico per la demo
        temperature=0.7,
        cache=MemoryCache()  # Cache per le risposte
    )
    
    # Configurazione del memory manager
    config = SummaryConfig(
        strategy=SummaryStrategy.KEEP_RECENT,
        trigger_turns=6,          # Trigger presto per la demo
        trigger_tokens=1500,      # Limite basso per test
        keep_recent_turns=2,      # Mantieni solo 2 turn recenti
        summary_max_tokens=150,   # Summary concisi
        auto_save_interval=3,     # Save frequente
        cache_summaries=True
    )
    
    # Inizializza manager
    memory_file = "demo_memory.json"
    manager = AdvancedMemoryManager(
        client=client, 
        config=config, 
        memory_file=memory_file,
        cache_type="memory"
    )
    
    print(f"Memory Manager inizializzato con strategia: {config.strategy.value}")
    print(f"File memoria: {memory_file}")
    print(f"Cache abilitata: {config.cache_summaries}")
    print()
    
    # Conversazione di esempio per dimostrare il summary
    demo_messages = [
        "Ciao! Sto pianificando un progetto di e-commerce con React e Node.js",
        "Quali sono i requisiti principali per l'autenticazione utente?",
        "Perfetto! Ora parliamo del database. Dovrei usare MongoDB o PostgreSQL?",
        "Interessante. E per il payment gateway? Stripe o PayPal?",
        "Ok, aggiungiamo anche la gestione dell'inventario. Come la structturiamo?",
        "Ottimo! Ora vorrei implementare un sistema di recensioni. Che ne pensi?",
        "Perfetto! Ultima cosa: come gestiamo le notifiche push?",
    ]
    
    try:
        for i, message in enumerate(demo_messages, 1):
            print(f"\n--- Messaggio {i} ---")
            print(f"👤 Utente: {message}")
            
            # Statistiche pre-messaggio
            stats_before = manager.get_memory_stats()
            print(f"📊 Memoria: {stats_before['current_metrics']['total_turns']} turn, ~{stats_before['current_metrics']['estimated_tokens']} token")
            
            # Invia messaggio
            response = manager.send_message(message)
            print(f"🤖 Bot: {response[:200]}{'...' if len(response) > 200 else ''}")
            
            # Statistiche post-messaggio
            stats_after = manager.get_memory_stats()
            if stats_after['current_metrics']['total_turns'] != stats_before['current_metrics']['total_turns']:
                reduction = stats_before['current_metrics']['estimated_tokens'] - stats_after['current_metrics']['estimated_tokens']
                if reduction > 0:
                    print(f"✂️ SUMMARY APPLICATO! Riduzione: {reduction} token")
                    if stats_after['last_summary']:
                        print(f"📝 Ultimo summary: {stats_after['last_summary']['summary'][:100]}...")
            
            print()
    
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrotta dall'utente")
    
    except Exception as e:
        logger.error(f"Errore durante demo: {e}")
        print(f"\n❌ Errore: {e}")
    
    finally:
        # Statistiche finali
        print("\n" + "="*50)
        print("📈 STATISTICHE FINALI")
        print("="*50)
        
        final_stats = manager.get_memory_stats()
        print(f"Turn totali: {final_stats['current_metrics']['total_turns']}")
        print(f"Token stimati: {final_stats['current_metrics']['estimated_tokens']}")
        print(f"Summary generati: {final_stats['summary_history_count']}")
        print(f"Strategia usata: {final_stats['current_strategy']}")
        print(f"Cache usata: {final_stats['cache_enabled']}")
        
        if final_stats['summary_history_count'] > 0:
            print(f"\nSummary generati:")
            for i, summary in enumerate(manager.summary_history[-3:], 1):  # Ultimi 3
                print(f"{i}. {summary['timestamp'][:19]} - {summary['summary'][:80]}...")
        
        print(f"\nFile memoria salvato: {memory_file}")
        print("Demo completata! 🎉")


if __name__ == "__main__":
    demo_advanced_memory()
