#!/usr/bin/env python3
"""
Esempio migliorato per la gestione del summary della memoria con DatapizzaAI.

Questo esempio migliora quello base del README aggiungendo:
- Configurazione flessibile 
- Metriche di base per monitoring
- Gestione errori migliorata
- Persistenza opzionale
- Logging utile per debug

È un buon equilibrio tra semplicità e funzionalità utili per la produzione.
"""

import os
import json
import time
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path

from dotenv import load_dotenv
from datapizza.clients import ClientFactory
from datapizza.memory import Memory
from datapizza.type import TextBlock, ROLE
from datapizza.cache import MemoryCache

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()


@dataclass
class MemoryConfig:
    """Configurazione per la gestione della memoria."""
    summarize_every: int = 8              # Ogni quanti turni fare summary
    max_summary_sentences: int = 5        # Lunghezza massima del summary
    keep_recent_turns: int = 3            # Turni recenti da mantenere sempre
    save_to_file: bool = False            # Salvataggio automatico su file
    memory_file: str = "memory.json"      # Nome del file di salvataggio
    importance_keywords: List[str] = None # Keywords per messaggi importanti
    
    def __post_init__(self):
        if self.importance_keywords is None:
            self.importance_keywords = [
                'importante', 'decisione', 'todo', 'problema', 'errore',
                'critico', 'urgente', 'deadline', 'requisito'
            ]


class ImprovedMemoryChat:
    """
    Chatbot con gestione intelligente della memoria.
    
    Migliora l'esempio base del README aggiungendo:
    - Configurazione flessibile
    - Metriche e logging
    - Gestione errori
    - Persistenza opzionale
    - Analisi messaggi importanti
    """
    
    def __init__(self, client, config: MemoryConfig = None):
        self.client = client
        self.config = config or MemoryConfig()
        self.memory = Memory()
        self.turns = 0
        self.summary_count = 0
        self.total_tokens_saved = 0
        
        # Carica memoria salvata se esiste
        if self.config.save_to_file:
            self._load_memory()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche sulla memoria."""
        total_chars = sum(
            len(str(block.content)) 
            for turn in self.memory 
            for block in turn.blocks 
            if hasattr(block, 'content')
        )
        
        return {
            'total_turns': len(self.memory),
            'total_characters': total_chars,
            'estimated_tokens': total_chars // 4,  # Stima approssimativa
            'summaries_created': self.summary_count,
            'estimated_tokens_saved': self.total_tokens_saved
        }
    
    def _has_important_content(self, content: str) -> bool:
        """Verifica se il contenuto contiene parole chiave importanti."""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.config.importance_keywords)
    
    def _should_preserve_turn(self, turn_index: int) -> bool:
        """Determina se un turn dovrebbe essere preservato (non riassunto)."""
        # Mantieni sempre gli ultimi N turni
        recent_threshold = len(self.memory) - self.config.keep_recent_turns
        if turn_index >= recent_threshold:
            return True
        
        # Verifica se contiene contenuto importante
        turn = self.memory[turn_index]
        for block in turn.blocks:
            if hasattr(block, 'content') and self._has_important_content(str(block.content)):
                return True
                
        return False
    
    def _generate_summary(self, turns_to_summarize: List[int]) -> str:
        """Genera un riassunto dei turni specificati."""
        if not turns_to_summarize:
            return ""
        
        # Costruisce il contesto dai turni da riassumere
        context_parts = []
        for turn_idx in turns_to_summarize:
            turn = self.memory[turn_idx]
            role_name = "Utente" if turn.role == ROLE.USER else "Assistente"
            
            for block in turn.blocks:
                if hasattr(block, 'content'):
                    content = str(block.content)[:400]  # Limita lunghezza per il prompt
                    context_parts.append(f"{role_name}: {content}")
        
        context = "\n".join(context_parts)
        
        prompt = f"""Riassumi questa conversazione in {self.config.max_summary_sentences} frasi concise.
Includi decisioni prese, informazioni importanti e task identificati.

CONVERSAZIONE:
{context}

RIASSUNTO:"""
        
        try:
            response = self.client.invoke(prompt)
            summary = response.text.strip()
            logger.info(f"Summary generato per {len(turns_to_summarize)} turni")
            return summary
            
        except Exception as e:
            logger.error(f"Errore generazione summary: {e}")
            # Fallback: riassunto semplice
            return f"[RIASSUNTO] Conversazione di {len(turns_to_summarize)} turni su vari argomenti."
    
    def _apply_smart_summary(self):
        """Applica strategia di summary intelligente."""
        if len(self.memory) < self.config.summarize_every:
            return
            
        logger.info(f"Applicando summary intelligente ({len(self.memory)} turni)")
        
        # Identifica turni da preservare e da riassumere
        turns_to_preserve = []
        turns_to_summarize = []
        
        for i in range(len(self.memory)):
            if self._should_preserve_turn(i):
                turns_to_preserve.append(i)
            else:
                turns_to_summarize.append(i)
        
        if not turns_to_summarize:
            logger.info("Nessun turn da riassumere (tutti importanti o recenti)")
            return
        
        # Salva metriche prima del summary
        stats_before = self.get_memory_stats()
        
        try:
            # Genera summary
            summary_text = self._generate_summary(turns_to_summarize)
            
            if not summary_text.strip():
                logger.warning("Summary vuoto generato, skip")
                return
            
            # Ricostruisce memoria
            new_memory = Memory()
            
            # Aggiungi summary come primo turn
            new_memory.add_turn([TextBlock(content=f"[Riassunto] {summary_text}")], ROLE.ASSISTANT)
            
            # Aggiungi turni preservati in ordine cronologico
            for turn_idx in sorted(turns_to_preserve):
                turn = self.memory[turn_idx]
                # Copia i blocks per evitare riferimenti condivisi
                new_blocks = []
                for block in turn.blocks:
                    if hasattr(block, 'content'):
                        new_blocks.append(TextBlock(content=block.content))
                    else:
                        new_blocks.append(block)  # Altri tipi di block
                new_memory.add_turn(new_blocks, turn.role)
            
            # Sostituisci memoria
            old_memory = self.memory
            self.memory = new_memory
            
            # Aggiorna statistiche
            stats_after = self.get_memory_stats()
            self.summary_count += 1
            self.total_tokens_saved += max(0, stats_before['estimated_tokens'] - stats_after['estimated_tokens'])
            
            logger.info(f"""Summary applicato con successo:
    - Turni: {stats_before['total_turns']} → {stats_after['total_turns']}
    - Token stimati: {stats_before['estimated_tokens']} → {stats_after['estimated_tokens']}
    - Turni preservati: {len(turns_to_preserve)}
    - Turni riassunti: {len(turns_to_summarize)}""")
            
            # Salva se configurato
            if self.config.save_to_file:
                self._save_memory()
                
        except Exception as e:
            logger.error(f"Errore durante summary: {e}")
            # In caso di errore, mantieni la memoria originale
    
    def send(self, user_input: str) -> str:
        """
        Invia messaggio e gestisce automaticamente il summary.
        
        Args:
            user_input: Il messaggio dell'utente
            
        Returns:
            La risposta del bot
        """
        # Aggiungi messaggio utente
        self.memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        try:
            # Genera risposta
            response = self.client.invoke(user_input, memory=self.memory)
            response_text = response.text
            
            # Aggiungi risposta alla memoria
            self.memory.add_turn([TextBlock(content=response_text)], ROLE.ASSISTANT)
            
            # Aggiorna contatore turni
            self.turns += 2  # User + Assistant
            
            # Applica summary se necessario
            if self.turns >= self.config.summarize_every:
                self._apply_smart_summary()
                self.turns = len(self.memory)  # Reset contatore dopo summary
            
            # Log metriche periodicamente
            if len(self.memory) % 10 == 0:
                stats = self.get_memory_stats()
                logger.info(f"Memoria: {stats['total_turns']} turni, "
                           f"~{stats['estimated_tokens']} token, "
                           f"{stats['summaries_created']} summary")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Errore durante invocazione: {e}")
            # Rimuovi l'ultimo messaggio utente se l'invocazione fallisce
            if self.memory and self.memory[-1].role == ROLE.USER:
                del self.memory[-1]
            raise
    
    def _save_memory(self):
        """Salva memoria su file."""
        if not self.config.memory_file:
            return
            
        try:
            memory_data = {
                'memory': self.memory.to_dict(),
                'turns': self.turns,
                'summary_count': self.summary_count,
                'total_tokens_saved': self.total_tokens_saved,
                'config': {
                    'summarize_every': self.config.summarize_every,
                    'max_summary_sentences': self.config.max_summary_sentences,
                    'keep_recent_turns': self.config.keep_recent_turns,
                    'importance_keywords': self.config.importance_keywords
                }
            }
            
            # Backup del file esistente
            memory_file = Path(self.config.memory_file)
            if memory_file.exists():
                backup_file = memory_file.with_suffix('.backup')
                memory_file.rename(backup_file)
            
            # Salva nuovo file
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Memoria salvata: {memory_file}")
            
        except Exception as e:
            logger.error(f"Errore salvataggio memoria: {e}")
    
    def _load_memory(self):
        """Carica memoria da file."""
        memory_file = Path(self.config.memory_file)
        if not memory_file.exists():
            return
            
        try:
            with open(memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Ricostruisci memoria
            if 'memory' in data:
                self.memory.clear()
                for turn_data in data['memory']:
                    from datapizza.type import Block
                    blocks = [Block.from_dict(block_data) for block_data in turn_data['blocks']]
                    self.memory.add_turn(blocks, ROLE(turn_data['role']))
            
            # Ripristina contatori
            self.turns = data.get('turns', 0)
            self.summary_count = data.get('summary_count', 0)
            self.total_tokens_saved = data.get('total_tokens_saved', 0)
            
            logger.info(f"Memoria caricata: {len(self.memory)} turni, {self.summary_count} summary")
            
        except Exception as e:
            logger.error(f"Errore caricamento memoria: {e}")
    
    def print_stats(self):
        """Stampa statistiche dettagliate."""
        stats = self.get_memory_stats()
        
        print("\n" + "="*50)
        print("📊 STATISTICHE MEMORIA")
        print("="*50)
        print(f"Turni attuali: {stats['total_turns']}")
        print(f"Caratteri totali: {stats['total_characters']:,}")
        print(f"Token stimati: {stats['estimated_tokens']:,}")
        print(f"Summary generati: {stats['summaries_created']}")
        print(f"Token risparmiati: ~{stats['estimated_tokens_saved']:,}")
        
        if self.config.save_to_file:
            print(f"File memoria: {self.config.memory_file}")
            
        print(f"Strategia: Smart summary ogni {self.config.summarize_every} turni")
        print(f"Turni recenti preservati: {self.config.keep_recent_turns}")
        print(f"Keywords importanti: {len(self.config.importance_keywords)}")
        print("="*50 + "\n")


def demo_improved_memory():
    """Demo dell'improved memory manager."""
    
    print("🚀 Demo Improved Memory Summary")
    print("="*40)
    
    # Client con cache (gestione robusta)
    try:
        client = ClientFactory.create(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",  # Modello economico per demo
            temperature=0.7,
            cache=MemoryCache()
        )
        logger.info("✅ Client con cache inizializzato correttamente")
    except Exception as cache_error:
        logger.warning(f"⚠️ Problema con cache, uso client senza cache: {cache_error}")
        client = ClientFactory.create(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
            temperature=0.7
            # Nessuna cache per evitare il bug
        )
    
    # Configurazione per demo (trigger frequente)
    config = MemoryConfig(
        summarize_every=6,        # Summary dopo 6 turni
        max_summary_sentences=4,  # Summary concisi  
        keep_recent_turns=2,      # Mantieni 2 turni recenti
        save_to_file=True,        # Salvataggio automatico
        memory_file="demo_improved_memory.json"
    )
    
    # Inizializza chat
    chat = ImprovedMemoryChat(client, config)
    
    print(f"✅ Chat inizializzata")
    print(f"📋 Summary ogni {config.summarize_every} turni")
    print(f"💾 Salvataggio: {config.save_to_file}")
    print(f"🔑 Keywords importanti: {len(config.importance_keywords)}")
    print()
    
    # Messaggi di esempio per dimostrare il sistema
    demo_messages = [
        "Ciao! Sto sviluppando un'app mobile per la gestione delle spese personali",
        "Che stack tecnologico mi consigli? React Native o Flutter?",
        "Perfetto! Per il backend pensavo a Node.js con PostgreSQL. Che ne pensi?",
        "Ottimo! Ora una cosa importante: come gestisco l'autenticazione degli utenti?",
        "Capito. E per la sincronizzazione dei dati offline/online?",
        "Grazie! Ah, un problema urgente: come proteggo i dati sensibili?",
        "Ultima domanda: consigli per il deployment su app store?",
    ]
    
    try:
        for i, message in enumerate(demo_messages, 1):
            print(f"\n--- Messaggio {i} ---")
            print(f"👤 Tu: {message}")
            
            # Statistiche prima del messaggio
            stats_before = chat.get_memory_stats()
            
            # Invia messaggio
            response = chat.send(message)
            print(f"🤖 Bot: {response[:150]}{'...' if len(response) > 150 else ''}")
            
            # Statistiche dopo il messaggio
            stats_after = chat.get_memory_stats()
            
            # Mostra se è stato applicato un summary
            if stats_after['summaries_created'] > stats_before['summaries_created']:
                saved_tokens = stats_before['estimated_tokens'] - stats_after['estimated_tokens']
                print(f"✂️ Summary applicato! Token risparmiati: ~{saved_tokens}")
            
            # Mostra metriche periodicamente
            if i % 3 == 0:
                print(f"📊 Memoria: {stats_after['total_turns']} turni, ~{stats_after['estimated_tokens']} token")
    
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrotta")
    
    except Exception as e:
        print(f"\n❌ Errore: {e}")
    
    finally:
        # Statistiche finali
        chat.print_stats()
        print("Demo completata! 🎉")


if __name__ == "__main__":
    demo_improved_memory()
