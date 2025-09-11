#!/usr/bin/env python3
"""
Chatbot semplice e funzionante con DatapizzAI
Supporta conversazioni con memoria, gestione errori e metriche di base.
"""

import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE
from datapizzai.cache import MemoryCache

class SimpleChatbot:
    """Chatbot semplice con memoria conversazionale"""
    
    def __init__(self, provider="openai", model="gpt-4o", temperature=0.7, use_cache=True):
        # Carica variabili d'ambiente
        load_dotenv()
        
        # Configura il client
        cache = MemoryCache() if use_cache else None
        
        self.client = ClientFactory.create(
            provider=provider,
            api_key=os.getenv(f"{provider.upper()}_API_KEY"),
            model=model,
            temperature=temperature,
            cache=cache
        )
        
        self.memory = Memory()
        self.conversation_count = 0
        
        print(f"🤖 Chatbot inizializzato con {provider}/{model}")
        if use_cache:
            print("💾 Cache attivata per ottimizzare le performance")
    
    def send_message(self, user_input: str) -> str:
        """Invia un messaggio al chatbot e riceve la risposta"""
        try:
            # Aggiungi il messaggio dell'utente alla memoria
            self.memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
            
            # Ottieni la risposta dal modello
            response = self.client.invoke("", memory=self.memory)
            
            # Aggiungi la risposta alla memoria
            self.memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
            # Aggiorna contatore conversazione
            self.conversation_count += 1
            
            # Mostra metriche di base
            total_tokens = (response.prompt_tokens_used or 0) + (response.completion_tokens_used or 0)
            print(f"📊 [Turno {self.conversation_count}] Token utilizzati: {total_tokens}")
            
            return response.text
            
        except Exception as e:
            print(f"❌ Errore durante la comunicazione: {str(e)}")
            return "Mi dispiace, si è verificato un errore. Riprova."
    
    def reset_conversation(self):
        """Resetta la memoria conversazionale"""
        self.memory = Memory()
        self.conversation_count = 0
        print("🔄 Conversazione resettata")
    
    def get_conversation_stats(self):
        """Mostra statistiche della conversazione"""
        print(f"📈 Statistiche conversazione:")
        print(f"   • Turni completati: {self.conversation_count}")
        print(f"   • Messaggi in memoria: {len(self.memory.turns) if hasattr(self.memory, 'turns') else 'N/A'}")

def main():
    """Funzione principale per avviare il chatbot"""
    print("🍕 DatapizzAI - Chatbot Semplice")
    print("=" * 40)
    
    # Verifica che le chiavi API siano configurate
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  ATTENZIONE: OPENAI_API_KEY non trovata nel file .env")
        print("   Crea un file .env con: OPENAI_API_KEY=sk-your-key-here")
        return
    
    try:
        # Inizializza il chatbot
        bot = SimpleChatbot(
            provider="openai",
            model="gpt-4o",
            temperature=0.7,
            use_cache=True
        )
        
        print("\n💬 Chat avviata! Comandi disponibili:")
        print("   • 'esci' o 'quit' - Termina la chat")
        print("   • 'reset' - Resetta la conversazione")
        print("   • 'stats' - Mostra statistiche")
        print("-" * 40)
        
        while True:
            try:
                # Input utente
                user_input = input("\n👤 Tu: ").strip()
                
                # Gestisci comandi speciali
                if user_input.lower() in ["esci", "exit", "quit"]:
                    print("👋 Arrivederci!")
                    break
                elif user_input.lower() == "reset":
                    bot.reset_conversation()
                    continue
                elif user_input.lower() == "stats":
                    bot.get_conversation_stats()
                    continue
                elif not user_input:
                    print("⚠️  Inserisci un messaggio valido")
                    continue
                
                # Invia messaggio e ricevi risposta
                response = bot.send_message(user_input)
                print(f"🤖 Bot: {response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interruzione da tastiera. Arrivederci!")
                break
            except Exception as e:
                print(f"❌ Errore imprevisto: {str(e)}")
                print("🔄 Riprova o digita 'esci' per terminare")
    
    except Exception as e:
        print(f"❌ Errore durante l'inizializzazione: {str(e)}")
        print("🔧 Verifica la configurazione e riprova")

if __name__ == "__main__":
    main()
