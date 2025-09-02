#!/usr/bin/env python3
"""
Esempio di utilizzo di DagPipeline con configurazione YAML
"""

import os
import sys
from pathlib import Path

# Aggiungi path per mymodules
sys.path.append(".")

from datapizzai.pipeline import DagPipeline

def main():
    print("🔄 Caricando DagPipeline da configurazione YAML...")
    
    try:
        # Crea istanza DagPipeline e carica configurazione YAML
        dag_pipeline = DagPipeline()
        dag_pipeline.from_yaml("dag_config.yaml")
        
        print("✅ DagPipeline caricata con successo da YAML")
        
        # Esegui pipeline con dati iniziali vuoti (i dati sono generati dai moduli)
        print("🔄 Eseguendo pipeline...")
        results = dag_pipeline.run({})
        
        print("✅ Pipeline completata con successo!")
        
        # Mostra risultati
        print(f"🎯 Nodi eseguiti: {list(results.keys())}")
        
        for node_name, node_result in results.items():
            if isinstance(node_result, dict):
                print(f"📊 {node_name}:")
                for key, value in node_result.items():
                    if isinstance(value, list) and len(value) > 0:
                        print(f"   {key}: {len(value)} elementi")
                    else:
                        print(f"   {key}: {value}")
            else:
                print(f"📊 {node_name}: {node_result}")
            
    except Exception as e:
        print(f"❌ Errore durante l'esecuzione: {e}")
        print("💡 Assicurati di:")
        print("   1. Essere nella directory examples/")
        print("   2. Avere il file dag_config.yaml")
        print("   3. Avere i moduli mymodules/")

if __name__ == "__main__":
    main()
