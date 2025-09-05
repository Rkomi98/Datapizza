#!/usr/bin/env python3
"""
Test completo dello stack di monitoring: Chatbot -> Prometheus -> Grafana
"""

import os
import time
import requests
from simple_chatbot_monitor import SimpleChatbotMonitor
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory

def test_prometheus_connection():
    """Testa la connessione a Prometheus"""
    try:
        response = requests.get("http://localhost:9090/-/ready", timeout=5)
        if response.status_code == 200:
            print("✅ Prometheus è raggiungibile")
            return True
        else:
            print(f"❌ Prometheus risponde con status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Errore connessione Prometheus: {e}")
        return False

def test_metrics_endpoint():
    """Testa l'endpoint delle metriche del chatbot"""
    try:
        response = requests.get("http://localhost:8000/metrics", timeout=5)
        if response.status_code == 200:
            print("✅ Endpoint metriche chatbot raggiungibile")
            return True
        else:
            print(f"❌ Endpoint metriche risponde con status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Errore connessione endpoint metriche: {e}")
        return False

def test_prometheus_query():
    """Testa una query Prometheus"""
    try:
        response = requests.get(
            "http://localhost:9090/api/v1/query?query=chatbot_requests_total",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                results = data["data"]["result"]
                print(f"✅ Query Prometheus riuscita: {len(results)} metriche trovate")
                return True
            else:
                print(f"❌ Query Prometheus fallita: {data}")
                return False
        else:
            print(f"❌ API Prometheus risponde con status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Errore query Prometheus: {e}")
        return False

def main():
    print("🔍 Test completo dello stack di monitoring\n")
    
    # Test 1: Prometheus
    print("1. Test connessione Prometheus...")
    if not test_prometheus_connection():
        print("💡 Avvia Prometheus con: ./start_monitoring.sh")
        return
    
    # Test 2: Endpoint metriche
    print("\n2. Test endpoint metriche chatbot...")
    if not test_metrics_endpoint():
        print("💡 Avvia il monitor del chatbot prima")
        return
    
    # Test 3: Query Prometheus
    print("\n3. Test query Prometheus...")
    if not test_prometheus_query():
        print("💡 Verifica la configurazione prometheus.yml")
        return
    
    # Test 4: Simulazione chatbot (se API key disponibile)
    print("\n4. Test simulazione chatbot...")
    if os.getenv("OPENAI_API_KEY"):
        try:
            print("🤖 Simulazione conversazione con monitoring...")
            monitor = SimpleChatbotMonitor("test-stack")
            client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
            memory = Memory()
            
            # Simulazione rapida
            response = monitor.monitor_chat("Ciao, questo è un test!", client, memory)
            print(f"✅ Conversazione test completata: {response.text[:50]}...")
            
            # Verifica che le metriche siano aggiornate
            time.sleep(2)
            response = requests.get(
                "http://localhost:9090/api/v1/query?query=chatbot_requests_total",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "success" and data["data"]["result"]:
                    total_requests = data["data"]["result"][0]["value"][1]
                    print(f"✅ Metriche aggiornate: {total_requests} richieste totali")
                else:
                    print("⚠️  Metriche non ancora aggiornate")
            
        except Exception as e:
            print(f"❌ Errore durante test chatbot: {e}")
    else:
        print("⚠️  OPENAI_API_KEY non configurata, salto il test del chatbot")
    
    print("\n🎉 Stack di monitoring funzionante!")
    print("\n📊 Accesso ai servizi:")
    print("  - Metriche chatbot: http://localhost:8000/metrics")
    print("  - Prometheus: http://localhost:9090")
    print("  - Grafana: http://localhost:3000 (admin/admin)")
    print("  - Zipkin: http://localhost:9411")

if __name__ == "__main__":
    main()
