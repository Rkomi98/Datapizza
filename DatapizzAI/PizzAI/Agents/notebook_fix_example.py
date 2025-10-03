#!/usr/bin/env python3
"""
Esempio corretto per il notebook - Sostituisci il tuo codice con questo
"""

from datapizza.clients import ClientFactory
from datapizza.memory import Memory
from datapizza.type import FunctionCallResultBlock, ROLE, TextBlock
from datapizza.tools.tools import tool
from dotenv import load_dotenv
import os

# Carica le variabili d'ambiente
load_dotenv()

# Definizione dei tool
@tool
def calcolatrice(operazione: str) -> str:
    """Esegue calcoli matematici semplici."""
    try:
        result = eval(operazione)
        return f"Il risultato di {operazione} è: {result}"
    except Exception as e:
        return f"Errore nel calcolo: {str(e)}"

@tool
def cerca_informazioni(argomento: str) -> str:
    """Cerca informazioni su un argomento specifico."""
    info_database = {
        "framework python ai": "I principali framework Python per AI sono: TensorFlow, PyTorch, scikit-learn, Keras, e Hugging Face Transformers. Ognuno ha i suoi punti di forza per diversi tipi di progetti AI.",
        "costo progetto ai": "I costi di un progetto AI variano ampiamente: da $10-100/mese per progetti piccoli fino a migliaia di dollari per progetti enterprise con GPU dedicate e grandi volumi di dati.",
        "python ai": "Python è il linguaggio più popolare per l'AI grazie alle sue librerie mature, community attiva e sintassi semplice."
    }
    
    for key, value in info_database.items():
        if argomento.lower() in key.lower():
            return f"Informazioni su '{argomento}': {value}"
    
    return f"Non ho informazioni specifiche su '{argomento}' nel mio database di esempio."

def chat_turn(user_input, memory, client, tools):
    """
    ✅ VERSIONE CORRETTA - Gestisce un singolo turno di conversazione con tools
    """
    print(f"👤 Utente: {user_input}")
    
    # Aggiungi input utente alla memoria
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    # Prima chiamata al modello
    response = client.invoke(
        input="",  # Input vuoto perché usiamo la memory
        memory=memory,
        tools=tools,
        tool_choice="auto"
        # ❌ NON usare tool_results qui!
    )
    
    # Gestione iterativa dei function calls
    while hasattr(response, "function_calls") and response.function_calls:
        print("🔧 Esecuzione tool calls...")
        
        # Aggiungi la risposta dell'assistant alla memoria
        memory.add_turn(response.content, ROLE.ASSISTANT)
        
        # Esegui ogni function call e aggiungi i risultati alla memoria
        for f_call in response.function_calls:
            print(f"   📞 {f_call.name}({f_call.arguments})")
            
            # Esegui il tool
            if f_call.name == "calcolatrice":
                result = calcolatrice(**(f_call.arguments or {}))
            elif f_call.name == "cerca_informazioni":
                result = cerca_informazioni(**(f_call.arguments or {}))
            else:
                result = f"Tool sconosciuto: {f_call.name}"
            
            print(f"   ✅ {result}")
            
            # Crea il blocco risultato
            tool_result_block = FunctionCallResultBlock(
                id=f_call.id,
                tool=f_call.name,
                result=result
            )
            
            # Aggiungi il risultato alla memoria come turn TOOL separato
            memory.add_turn([tool_result_block], ROLE.TOOL)
        
        # Richiedi risposta finale al modello
        response = client.invoke(
            input="",  # Input vuoto perché usiamo la memory
            memory=memory,
            tools=tools,
            tool_choice="auto"
            # ❌ NON usare tool_results qui!
        )
    
    # Aggiungi la risposta finale alla memoria
    if response.text:
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        print(f"🤖 Assistant: {response.text}")

# Esempio di utilizzo
if __name__ == "__main__":
    # Setup
    client = ClientFactory.create(
        provider="openai", 
        api_key=os.getenv("OPENAI_API_KEY"), 
        model="gpt-4o-mini"
    )
    
    tools = [calcolatrice, cerca_informazioni]
    memory = Memory()
    
    # Conversazione di esempio
    conversation = [
        "Ciao! Sono Mirko, sto lavorando su un progetto AI",
        "Cerca informazioni sui framework Python per AI", 
        "Calcola il costo se spendo 500€ al mese per 2 anni",
        "Ricordi il mio nome e cosa sto facendo?"
    ]
    
    print("🤖 Conversazione con DatapizzaAI")
    print("=" * 50)
    
    for user_input in conversation:
        chat_turn(user_input, memory, client, tools)
        print()  # Spazio tra turni
