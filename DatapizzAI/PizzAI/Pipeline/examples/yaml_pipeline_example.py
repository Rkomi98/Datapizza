#!/usr/bin/env python3
"""
Esempio di utilizzo di FunctionalPipeline con configurazione YAML.

Questo esempio dimostra:
- Caricamento pipeline da file YAML
- Moduli personalizzati esterni
- Pipeline complessa multi-step
- Gestione parametri nei moduli

Requisiti:
- File YAML di configurazione
- Moduli custom in mymodules/
"""

import os
import sys
from pathlib import Path

# Aggiungi la directory corrente al path per importare mymodules
sys.path.append(str(Path(__file__).parent))

from datapizzai.pipeline import FunctionalPipeline


def main():
    print("🔄 Caricando FunctionalPipeline da configurazione YAML...")
    
    # Path del file YAML di configurazione
    yaml_config_path = "functional_pipeline_config.yaml"
    
    if not os.path.exists(yaml_config_path):
        print(f"❌ File di configurazione {yaml_config_path} non trovato!")
        return
    
    try:
        # Carica pipeline da YAML
        pipeline = FunctionalPipeline.from_yaml(yaml_config_path)
        print("✅ Pipeline caricata con successo da YAML")
        
        # Mostra struttura della pipeline
        print("\n📋 Moduli caricati dalla configurazione:")
        print("   • DocumentLoader (da mymodules.loaders)")
        print("   • TextProcessor (da mymodules.processors)")
        print("   • DataValidator (da mymodules.processors)")
        print("   • ReportBuilder (da mymodules.processors)")
        
        print("\n🔗 Sequenza pipeline:")
        print("   load_data → process → validate → build_report")
        
        print("\n🚀 Eseguendo pipeline...")
        
        # Esegui pipeline
        results = pipeline.execute()
        
        print("✅ Pipeline completata con successo!")
        
        # Mostra risultati
        if "build_report" in results:
            print("\n" + "="*60)
            print(results["build_report"]["final_report"])
        
        # Mostra statistiche dettagliate
        print("\n" + "="*60)
        print("📊 STATISTICHE ESECUZIONE:")
        
        for step_name, step_result in results.items():
            print(f"\n🔸 {step_name.upper()}:")
            
            if step_name == "load_data":
                print(f"   Documenti caricati: {step_result.get('count', 0)}")
                print(f"   Fonte: {step_result.get('source', 'unknown')}")
            
            elif step_name == "process":
                print(f"   Documenti processati: {step_result.get('total_processed', 0)}")
                print(f"   Documenti validi: {step_result.get('valid_documents', 0)}")
                print(f"   Filtrati: {step_result.get('filtered_out', 0)}")
            
            elif step_name == "validate":
                summary = step_result.get('validation_summary', {})
                print(f"   Documenti controllati: {summary.get('total_checked', 0)}")
                print(f"   Validi: {summary.get('valid_count', 0)}")
                print(f"   Non validi: {summary.get('invalid_count', 0)}")
            
            elif step_name == "build_report":
                metadata = step_result.get('report_metadata', {})
                print(f"   Report generato: {metadata.get('total_lines', 0)} righe")
                print(f"   Documenti nel report: {metadata.get('documents_processed', 0)}")
        
        print(f"\n🎯 Pipeline eseguita tramite YAML configuration!")
        
    except Exception as e:
        print(f"❌ Errore durante l'esecuzione della pipeline: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


