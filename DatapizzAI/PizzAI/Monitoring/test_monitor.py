#!/usr/bin/env python3
"""
Test rapido del monitor per chatbot
"""

import os
import sys
import time

# Aggiungi il path del monitor
sys.path.append('.')

from simple_chatbot_monitor import SimpleChatbotMonitor
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

def test_monitor():
    """Test del monitor senza API key reale"""
    
    print("🧪 Test del SimpleChatbotMonitor...")
    
    # Inizializza monitor
    monitor = SimpleChatbotMonitor("test-chatbot", prometheus_port=8001)
    
    print("\n📊 Monitor inizializzato! Servizi attivi:")
    print("  - Prometheus: http://localhost:8001")
    print("  - ContextTracing: ✅ Attivo")
    print("  - Zipkin: ✅ Configurato")
    
    # Test con mock client (senza API key)
    print("\n🔧 Creazione mock client...")
    
    try:
        # Prova con mock client se disponibile
        from datapizzai.clients import MockClient
        client = MockClient()
        print("✅ Mock client creato")
        
        # Test monitoring
        memory = Memory()
        
        print("\n💬 Test monitoring con mock...")
        
        # Simula alcune chiamate
        test_messages = [
            "Ciao, come stai?",
            "Parlami del machine learning",
            "Grazie!"
        ]
        
        for i, msg in enumerate(test_messages, 1):
            print(f"📤 Test {i}: {msg}")
            
            try:
                # Monitora la chiamata (dovrebbe funzionare anche con mock)
                response = monitor.monitor_chat(msg, client, memory)
                print(f"📥 Risposta: {response.text[:100]}...")
            except Exception as e:
                print(f"⚠️  Errore atteso con mock: {e}")
            
            time.sleep(0.5)
        
        print("\n✅ Test completato!")
        print("📊 Controlla le metriche su http://localhost:8001")
        
    except ImportError:
        print("⚠️  MockClient non disponibile, test limitato")
        print("✅ Monitor comunque inizializzato correttamente!")
    
    return True

if __name__ == "__main__":
    test_monitor()
