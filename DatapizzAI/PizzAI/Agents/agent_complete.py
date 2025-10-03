"""
DATAPIZZA AGENTS - GUIDA COMPLETA END-TO-END
===========================================

Questo file fornisce una guida completa per l'utilizzo di tutti gli agenti 
e funzionalità disponibili nella libreria datapizza.

Autore: DatapizzaAI Framework
Versione: 3.0.8
"""

import os
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any

# Import dei moduli principali di datapizza
from datapizza.agents import Agent, ClientManager
from datapizza.clients import ClientFactory, MockClient
from datapizza.clients.factory import Provider
from datapizza.tools import tool, Tool
from datapizza.memory import Memory
from datapizza.type import ROLE, TextBlock
from datapizza.pipeline import IngestionPipeline
from datapizza.vectorstores import QdrantVectorstore, Distance

from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()


class DatapizzaAIAgentDemo:
    """
    Classe demo per dimostrare tutte le funzionalità degli agenti DatapizzaAI.
    """
    
    def __init__(self):
        self.client = None
        self.agent = None
        self.memory = Memory()
        self.results = {}
        
    def setup_client(self, provider: Any = "openai", api_key: str = None, model: str = None, system_prompt: str = "", temperature: float = 0.7):
        """
        1. CONFIGURAZIONE CLIENT
        ========================
        
        DatapizzaAI supporta multiple provider di LLM:
        - OpenAI (GPT-3.5-turbo, GPT-4, GPT-4-turbo, etc.)
        - Google (Gemini Pro, Gemini Pro Vision)  
        - Anthropic (Claude-3, Claude-3.5-sonnet, etc.)
        - Mistral (mistral-large, mistral-medium, etc.)
        - Azure OpenAI
        """
        
        # Normalizza provider (supporta enum Provider o stringa)
        provider_key = getattr(provider, 'value', provider)
        
        # Configurazione API key (da environment variable per sicurezza)
        if not api_key:
            env_map = {
                "openai": "OPENAI_API_KEY",
                "google": "GOOGLE_API_KEY", 
                "anthropic": "ANTHROPIC_API_KEY",
                "mistral": "MISTRAL_API_KEY",
                "azure_openai": "AZURE_OPENAI_API_KEY"
            }
            api_key = os.getenv(env_map.get(str(provider_key)))
            
        # Se non è disponibile una API key, utilizza un client di mock per permettere i test locali
        use_mock = False
        if not api_key:
            use_mock = True
            
        # Configurazione modelli di default per provider
        default_models = {
            "openai": "gpt-4o",
            "google": "gemini-2.0-flash",
            "anthropic": "claude-3.5-sonnet",
            "mistral": "mistral-large",
        }
        
        if not model:
            model = default_models.get(str(provider_key), "gpt-3.5-turbo")
            
        provider_name = str(provider_key).upper()
        print(f"📡 Configurazione client {provider_name} con modello {model}")

        # Creazione del client: se mancano le credenziali, fallback al MockClient
        if use_mock:
            print("⚠️  API key non trovata: utilizzo MockClient per test locali")
            self.client = MockClient(model_name=model, system_prompt=system_prompt, temperature=temperature)
        else:
            self.client = ClientFactory.create(
                provider=provider,
                api_key=api_key,
                model=model,
                system_prompt=system_prompt,
                temperature=temperature
            )
        
        # Configurazione client globale (opzionale)
        ClientManager.set_global_client(self.client)
        
        print("✅ Client configurato con successo!")
        return self.client
    
    def create_custom_tools(self) -> List[Tool]:
        """
        2. CREAZIONE TOOLS PERSONALIZZATI  
        =================================
        
        I tools permettono agli agenti di eseguire azioni specifiche
        come calcoli, ricerche, manipolazione dati, etc.
        """
        
        @tool(name="calculator", description="Esegue calcoli matematici")
        def calculator(expression: str) -> str:
            """Calcola un'espressione matematica in modo sicuro."""
            try:
                # Sicurezza: evalua solo espressioni matematiche semplici
                allowed_chars = set('0123456789+-*/.()')
                if not all(c in allowed_chars or c.isspace() for c in expression):
                    return "Errore: caratteri non consentiti nell'espressione"
                
                result = eval(expression)
                return f"Risultato: {result}"
            except Exception as e:
                return f"Errore nel calcolo: {str(e)}"
        
        @tool(name="weather_info", description="Fornisce informazioni meteo simulate")
        def weather_info(city: str) -> str:
            """Simula informazioni meteo per una città."""
            # Simulazione dati meteo
            weather_data = {
                "Roma": {"temp": "22°C", "condizioni": "Soleggiato"},
                "Milano": {"temp": "18°C", "condizioni": "Nuvoloso"}, 
                "Napoli": {"temp": "25°C", "condizioni": "Parzialmente nuvoloso"},
                "Torino": {"temp": "16°C", "condizioni": "Pioggia leggera"}
            }
            
            data = weather_data.get(city, {"temp": "20°C", "condizioni": "Variabile"})
            return f"Meteo per {city}: {data['temp']}, {data['condizioni']}"
        
        @tool(name="save_data", description="Salva dati in un file JSON")
        def save_data(data: str, filename: str = "agent_output.json") -> str:
            """Salva i dati forniti in un file JSON."""
            try:
                # Tenta di parsare come JSON, altrimenti salva come stringa
                try:
                    json_data = json.loads(data)
                except json.JSONDecodeError:
                    json_data = {"content": data, "timestamp": str(datetime.now())}
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                
                return f"Dati salvati in {filename}"
            except Exception as e:
                return f"Errore nel salvataggio: {str(e)}"
        
        @tool(name="text_analysis", description="Analizza un testo fornendo statistiche")
        def text_analysis(text: str) -> str:
            """Analizza un testo e fornisce statistiche."""
            words = text.split()
            sentences = text.split('.')
            
            analysis = {
                "caratteri": len(text),
                "parole": len(words),
                "frasi": len([s for s in sentences if s.strip()]),
                "parola_media": sum(len(w) for w in words) / len(words) if words else 0
            }
            
            return json.dumps(analysis, indent=2)
        
        tools = [calculator, weather_info, save_data, text_analysis]
        print(f"🔧 Creati {len(tools)} tools personalizzati")
        return tools
    
    def setup_agent_basic(self, tools: List[Tool] = None) -> Agent:
        """
        3. AGENTE BASE
        ==============
        
        Creazione di un agente con configurazioni base.
        """
        
        if not self.client:
            raise ValueError("Client non configurato. Eseguire setup_client() prima.")
            
        system_prompt = """
        Sei un assistente AI intelligente e versatile chiamato DatapizzaAI Agent.
        
        Le tue capacità includono:
        - Analisi e elaborazione di testi
        - Calcoli matematici usando il tool calculator
        - Informazioni meteo usando il tool weather_info  
        - Salvataggio dati usando il tool save_data
        - Analisi testuale usando il tool text_analysis
        
        Rispondi sempre in italiano e sii preciso e utile.
        Utilizza i tools a tua disposizione quando necessario.
        """
        
        self.agent = Agent(
            name="DatapizzaAI_Agent_Basic",
            client=self.client,
            system_prompt=system_prompt,
            tools=tools or [],
            max_steps=5,  # Massimo 5 step di ragionamento
            terminate_on_text=True,  # Termina quando produce testo
            stateless=False,  # Mantiene memoria tra le chiamate
            memory=self.memory
        )
        
        print("🤖 Agente base creato con successo!")
        return self.agent
        
    def setup_agent_advanced(self, tools: List[Tool] = None) -> Agent:
        """
        4. AGENTE AVANZATO CON PLANNING
        ===============================
        
        Agente con funzionalità di planning per task complessi.
        """
        
        if not self.client:
            raise ValueError("Client non configurato. Eseguire setup_client() prima.")
            
        system_prompt = """
        Sei un agente AI avanzato con capacità di planning strategico.
        
        Per ogni task complesso:
        1. Analizza il problema
        2. Crea un piano strutturato
        3. Esegui i passi del piano usando i tools
        4. Verifica i risultati
        5. Fornisci una sintesi finale
        
        Tools disponibili:
        - calculator: per calcoli matematici
        - weather_info: per informazioni meteo
        - save_data: per salvare risultati
        - text_analysis: per analisi testi
        
        Sii metodico e preciso nel tuo approccio.
        """
        
        self.agent = Agent(
            name="DatapizzaAI_Agent_Advanced",
            client=self.client,
            system_prompt=system_prompt,
            tools=tools or [],
            max_steps=10,  # Più step per task complessi
            terminate_on_text=True,
            stateless=False,
            planning_interval=3,  # Planning ogni 3 step
            memory=self.memory,
            stream=False  # Non streaming per default
        )
        
        print("🎯 Agente avanzato con planning creato!")
        return self.agent
        
    def setup_multi_agent_system(self) -> Dict[str, Agent]:
        """
        5. SISTEMA MULTI-AGENT
        ======================
        
        Creazione di un sistema con agenti specializzati.
        """
        
        if not self.client:
            raise ValueError("Client non configurato. Eseguire setup_client() prima.")
        
        # Agente Analista  
        analyst_agent = Agent(
            name="Analyst_Agent",
            client=self.client,
            system_prompt="""
            Sei un agente specializzato nell'analisi dati e testi.
            Il tuo compito è analizzare informazioni e fornire insight dettagliati.
            Usa il tool text_analysis per analisi approfondite.
            """,
            tools=[self.create_custom_tools()[3]],  # Solo text_analysis
            max_steps=3,
            stateless=False
        )
        
        # Agente Calcolatore
        calculator_agent = Agent(
            name="Calculator_Agent", 
            client=self.client,
            system_prompt="""
            Sei un agente specializzato nei calcoli matematici e statistici.
            Risolvi problemi matematici complessi usando il calculator.
            Fornisci spiegazioni step-by-step.
            """,
            tools=[self.create_custom_tools()[0]],  # Solo calculator
            max_steps=3,
            stateless=False
        )
        
        # Agente Coordinatore
        coordinator_agent = Agent(
            name="Coordinator_Agent",
            client=self.client,
            system_prompt="""
            Sei l'agente coordinatore che gestisce gli altri agenti.
            Analizza le richieste e decidi quale agente specializzato utilizzare.
            Coordina le risposte per fornire risultati completi.
            """,
            tools=[],
            max_steps=5,
            stateless=False,
            can_call=[analyst_agent, calculator_agent]  # Può chiamare altri agenti
        )
        
        agents = {
            "analyst": analyst_agent,
            "calculator": calculator_agent, 
            "coordinator": coordinator_agent
        }
        
        print("🔗 Sistema multi-agent configurato!")
        return agents
    
    def demonstrate_memory_usage(self):
        """
        6. GESTIONE MEMORIA
        ===================
        
        Dimostra l'uso avanzato della memoria conversazionale.
        """
        
        print("\n💾 Demo gestione memoria:")
        
        # Creazione memoria personalizzata
        custom_memory = Memory()
        
        # Aggiunta di context iniziale
        custom_memory.add_turn(
            TextBlock(content="Ricorda che l'utente preferisce risposte concise."),
            role=ROLE.SYSTEM
        )
        
        # Aggiunta conversazione simulata
        custom_memory.add_turn(
            TextBlock(content="Come stai oggi?"),
            role=ROLE.USER
        )
        
        custom_memory.add_turn(
            TextBlock(content="Sto bene, grazie! Come posso aiutarti?"),
            role=ROLE.ASSISTANT
        )
        
        print(f"Memoria creata con {len(custom_memory.memory)} turn")
        
        # Uso memoria con agente
        if self.agent:
            self.agent._memory = custom_memory
            print("✅ Memoria personalizzata applicata all'agente")
        
        return custom_memory
    
    def demonstrate_streaming(self, query: str) -> str:
        """
        7. STREAMING DELLE RISPOSTE
        ===========================
        
        Dimostra l'uso dello streaming per risposte real-time.
        """
        
        if not self.agent:
            raise ValueError("Agente non configurato.")
        
        print(f"\n🔄 Streaming risposta per: '{query}'")
        print("-" * 50)
        
        full_response = ""
        step_count = 0
        
        for chunk in self.agent.stream_invoke(query):
            if isinstance(chunk, str):
                # Risposta finale
                full_response = chunk
                print(f"\n✅ Risposta completa ricevuta")
            else:
                # Step intermedio
                step_count += 1
                print(f"Step {step_count}: {type(chunk).__name__}")
                
        print("-" * 50)
        return full_response
    
    async def demonstrate_async_usage(self, query: str) -> str:
        """
        8. UTILIZZO ASINCRONO
        ====================
        
        Dimostra l'uso asincrono degli agenti per performance migliori.
        """
        
        if not self.agent:
            raise ValueError("Agente non configurato.")
        
        print(f"\n⚡ Esecuzione asincrona per: '{query}'")
        
        # Esecuzione asincrona standard
        result = await self.agent.a_run(query)
        
        print("✅ Esecuzione asincrona completata")
        return result
    
    def run_comprehensive_demo(self):
        """
        9. DEMO COMPLETA
        ================
        
        Esegue una dimostrazione completa di tutte le funzionalità.
        """
        
        print("🚀 AVVIO DEMO COMPLETA DATAPIZZA AGENTS")
        print("=" * 60)
        
        # 1. Setup client (OpenAI di default)
        try:
            self.setup_client()
        except ValueError as e:
            print(f"❌ Errore configurazione client: {e}")
            print("💡 Assicurati di impostare OPENAI_API_KEY nelle variabili d'ambiente")
            return
        
        # 2. Creazione tools
        tools = self.create_custom_tools()
        
        # 3. Creazione agente base
        self.setup_agent_basic(tools)
        
        # 4. Test funzionalità base
        print("\n📋 Test funzionalità base:")
        
        test_queries = [
            "Calcola il risultato di 25 * 4 + 100",
            "Che tempo fa a Roma?", 
            "Analizza questo testo: 'DatapizzaAI è un framework potente per la creazione di agenti intelligenti.'",
        ]
        
        for query in test_queries:
            print(f"\n❓ Query: {query}")
            try:
                response = self.agent.run(query)
                print(f"💬 Risposta: {response}")
                self.results[query] = response
            except Exception as e:
                print(f"❌ Errore: {str(e)}")
        
        # 5. Test streaming
        print("\n🔄 Test streaming:")
        try:
            self.demonstrate_streaming("Dimmi tre curiosità interessanti sull'AI")
        except Exception as e:
            print(f"❌ Errore streaming: {str(e)}")
        
        # 6. Test memoria
        self.demonstrate_memory_usage()
        
        # 7. Setup agente avanzato
        print("\n🎯 Configurazione agente avanzato...")
        self.setup_agent_advanced(tools)
        
        # 8. Test agente avanzato con task complesso
        complex_query = """
        Voglio pianificare una gita a Roma. Aiutami a:
        1. Controllare il meteo
        2. Calcolare il budget per 3 persone (300 euro a persona)
        3. Salvare le informazioni in un file
        """
        
        print(f"\n🧠 Test agente avanzato:")
        print(f"❓ Query complessa: {complex_query}")
        
        try:
            response = self.agent.run(complex_query)
            print(f"💬 Risposta: {response}")
            self.results["complex_query"] = response
        except Exception as e:
            print(f"❌ Errore: {str(e)}")
        
        # 9. Test multi-agent
        print("\n🔗 Setup sistema multi-agent...")
        try:
            agents = self.setup_multi_agent_system()
            coordinator = agents["coordinator"]
            
            multi_query = "Analizza il testo 'AI revolution' e calcola 2^8"
            print(f"❓ Query multi-agent: {multi_query}")
            
            response = coordinator.run(multi_query)
            print(f"💬 Risposta coordinatore: {response}")
            self.results["multi_agent"] = response
            
        except Exception as e:
            print(f"❌ Errore multi-agent: {str(e)}")
        
        # 10. Riepilogo finale
        print("\n📊 RIEPILOGO DEMO:")
        print("=" * 60)
        print(f"✅ Queries elaborate: {len(self.results)}")
        print(f"🔧 Tools utilizzati: {len(tools)}")
        print(f"🤖 Agenti creati: 4 (base, avanzato, analista, calcolatore, coordinatore)")
        print(f"💾 Memoria: {len(self.memory.memory)} turn salvati")
        
        return self.results
    
    async def run_async_demo(self):
        """
        10. DEMO ASINCRONA
        ==================
        
        Esegue test delle funzionalità asincrone.
        """
        
        print("\n⚡ DEMO FUNZIONALITÀ ASINCRONE")
        print("=" * 40)
        
        if not self.agent:
            print("❌ Agente non configurato")
            return
        
        async_queries = [
            "Racconta una storia breve",
            "Spiega cos'è l'intelligenza artificiale", 
            "Calcola 15 * 23 + 45"
        ]
        
        # Esecuzione parallela di query
        import time
        
        print("🔄 Esecuzione sequenziale:")
        start_time = time.time()
        
        for query in async_queries:
            result = await self.demonstrate_async_usage(query)
            print(f"Query: {query[:30]}... -> Completata")
        
        sequential_time = time.time() - start_time
        
        print(f"⏱️ Tempo sequenziale: {sequential_time:.2f}s")
        
        # Esecuzione parallela
        print("\n⚡ Esecuzione parallela:")
        start_time = time.time()
        
        tasks = [self.agent.a_run(query) for query in async_queries]
        results = await asyncio.gather(*tasks)
        
        parallel_time = time.time() - start_time
        
        print(f"⏱️ Tempo parallelo: {parallel_time:.2f}s")
        print(f"🚀 Speedup: {sequential_time/parallel_time:.2fx}")
        
        return results


# Funzioni helper per l'utilizzo
def quick_start_guide():
    """
    GUIDA RAPIDA
    ============
    
    Funzione helper per iniziare velocemente.
    """
    print("🚀 DATAPIZZA AGENTS - GUIDA RAPIDA")
    print("=" * 50)
    print()
    print("1. Imposta variabile d'ambiente:")
    print("   export OPENAI_API_KEY='your-api-key-here'")
    print()
    print("2. Esegui demo completa:")
    print("   demo = DatapizzaAIAgentDemo()")
    print("   demo.run_comprehensive_demo()")
    print()
    print("3. Per uso asincrono:")
    print("   await demo.run_async_demo()")
    print()
    print("4. Per configurazioni avanzate vedi la documentazione completa.")
    print()


def example_usage():
    """
    ESEMPIO D'USO RAPIDO
    ===================
    
    Esempio minimo per iniziare.
    """
    
    print("💡 Esempio d'uso minimo:")
    print("-" * 30)
    
    # Setup rapido
    demo = DatapizzaAIAgentDemo()
    
    try:
        # Configurazione
        demo.setup_client()
        tools = demo.create_custom_tools()
        demo.setup_agent_basic(tools)
        
        # Test singolo
        response = demo.agent.run("Calcola 10 + 20 e dimmi il risultato")
        print(f"Risposta: {response}")
        
    except Exception as e:
        print(f"Errore: {e}")
        print("Assicurati di configurare OPENAI_API_KEY")


# Punto di ingresso principale
if __name__ == "__main__":
    # Mostra guida rapida
    quick_start_guide()
    
    # Chiedi all'utente cosa fare
    print("Scegli un'opzione:")
    print("1. Demo completa")
    print("2. Esempio rapido") 
    print("3. Solo guida")
    
    choice = input("Inserisci scelta (1-3): ").strip()
    
    if choice == "1":
        print("\n🚀 Avvio demo completa...")
        demo = DatapizzaAIAgentDemo()
        demo.run_comprehensive_demo()
        
    elif choice == "2":
        print("\n💡 Esempio rapido...")
        example_usage()
        
    else:
        print("\n📚 Guida visualizzata. Per maggiori dettagli leggi il codice!")
        
    print("\n✅ Demo completata! Controlla i file salvati per i risultati.")
