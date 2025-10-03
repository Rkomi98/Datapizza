#!/usr/bin/env python3
"""
Test corretto per l'uso dei tools con datapizza
Questo esempio mostra come usare correttamente la Memory per gestire i tool results
"""

import os
from dotenv import load_dotenv
from datapizza.clients import ClientFactory
from datapizza.memory import Memory
from datapizza.type import FunctionCallResultBlock, ROLE
from datapizza.tools.tools import tool

# Carica le variabili d'ambiente
load_dotenv()

# Definizione dei tool
@tool
def calcolatrice(operazione: str) -> str:
    """
    Esegue calcoli matematici semplici.
    
    Args:
        operazione: L'operazione matematica da eseguire (es. "2 + 3", "10 * 5")
    
    Returns:
        Il risultato del calcolo come stringa
    """
    try:
        # Valutazione sicura dell'operazione matematica
        result = eval(operazione)
        return f"Il risultato di {operazione} è: {result}"
    except Exception as e:
        return f"Errore nel calcolo: {str(e)}"

@tool
def cerca_informazioni(argomento: str) -> str:
    """
    Cerca informazioni su un argomento specifico.
    
    Args:
        argomento: L'argomento su cui cercare informazioni
    
    Returns:
        Informazioni sull'argomento richiesto
    """
    # Simulazione di una ricerca
    info_database = {
        "python type hints": "I Python type hints sono annotazioni che indicano il tipo di dati previsto per variabili, parametri di funzioni e valori di ritorno. Introdotti in Python 3.5 con PEP 484, migliorano la leggibilità del codice e supportano il controllo statico dei tipi.",
        "machine learning": "Il machine learning è un sottoinsieme dell'intelligenza artificiale che permette ai computer di apprendere e migliorare automaticamente attraverso l'esperienza senza essere esplicitamente programmati.",
        "datapizza": "DatapizzaAI è una libreria Python per l'integrazione con vari modelli di intelligenza artificiale, fornendo un'interfaccia unificata per diversi provider come OpenAI, Anthropic, Google, ecc."
    }
    
    # Cerca informazioni (case-insensitive)
    for key, value in info_database.items():
        if argomento.lower() in key.lower():
            return f"Informazioni su '{argomento}': {value}"
    
    return f"Non sono state trovate informazioni specifiche su '{argomento}'. Questo è un database di esempio limitato."

def test_tools_workflow():
    """Test del workflow completo con tools e memory"""
    
    # Verifica che la chiave API sia presente
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  Errore: OPENAI_API_KEY non trovata nel file .env")
        print("Assicurati di avere un file .env con:")
        print("OPENAI_API_KEY=sk-...")
        return
    
    print("🚀 Inizializzo il client DatapizzaAI...")
    
    # Crea il client
    try:
        client = ClientFactory.create(
            provider="openai", 
            api_key=api_key, 
            model="gpt-4o-mini"
        )
        print("✅ Client creato con successo")
    except Exception as e:
        print(f"❌ Errore nella creazione del client: {e}")
        return
    
    # Crea tools e memory
    tools = [calcolatrice, cerca_informazioni]
    memory = Memory()
    
    print("\n📋 Tools disponibili:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Prima richiesta
    user_input = "Calcola (25 * 4) + 10 e cerca informazioni su Python type hints"
    print(f"\n👤 Utente: {user_input}")
    
    try:
        response = client.invoke(
            input=user_input,
            tools=tools,
            tool_choice="auto",
            memory=memory
        )
        print(f"🤖 Assistant: {response.text}")
        
        # Gestione iterativa dei function calls
        iteration = 0
        while hasattr(response, "function_calls") and response.function_calls:
            iteration += 1
            print(f"\n🔧 Iterazione {iteration} - Esecuzione tool calls:")
            
                        # Aggiungi la risposta dell'assistant alla memoria
            memory.add_turn(response.content, ROLE.ASSISTANT)
            
            # Crea i risultati dei tool e aggiungili uno per volta alla memoria
            for f_call in response.function_calls:
                print(f"   📞 Chiamata: {f_call.name}({f_call.arguments})")
                
                tool_name = f_call.name
                args = f_call.arguments or {}
                
                if tool_name == "calcolatrice":
                    result = calcolatrice(**args)
                elif tool_name == "cerca_informazioni":
                    result = cerca_informazioni(**args)
                else:
                    result = f"Tool sconosciuto: {tool_name}"
                
                print(f"   ✅ Risultato: {result}")
                
                tool_result_block = FunctionCallResultBlock(
                    id=f_call.id,
                    tool=tool_name,
                    result=result,
                )
                
                # Aggiungi ogni tool result come turn separato con ruolo TOOL
                memory.add_turn([tool_result_block], ROLE.TOOL)
            
            # Re-invoca con la memoria aggiornata
            response = client.invoke(
                input="",
                tools=tools,
                tool_choice="auto",
                memory=memory
            )
            
            if response.text:
                print(f"🤖 Assistant: {response.text}")
        
        print("\n✅ Test completato con successo!")
        
    except Exception as e:
        print(f"❌ Errore durante l'esecuzione: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Test del workflow DatapizzaAI con tools")
    print("=" * 50)
    test_tools_workflow()
