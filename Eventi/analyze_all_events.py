#!/usr/bin/env python3
"""
Script per analizzare tutti gli eventi nella cartella e generare l'indice per la dashboard.
"""

import os
import json
from pathlib import Path
from analyze_event import EventAnalyzer


def find_event_folders(base_path: str = '.') -> list:
    """Trova tutte le cartelle evento (cartelle contenenti file CSV)."""
    base_path = Path(base_path)
    event_folders = []
    
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Verifica se contiene almeno un CSV
            csv_files = list(item.glob('*.csv'))
            if csv_files:
                event_folders.append(item)
    
    return event_folders


def analyze_all_events():
    """Analizza tutti gli eventi e genera l'indice."""
    print("\n" + "=" * 70)
    print("🎯 ANALISI COMPLETA EVENTI DATAPIZZA")
    print("=" * 70)
    
    # Trova tutte le cartelle evento
    event_folders = find_event_folders()
    
    if not event_folders:
        print("\n⚠️  Nessuna cartella evento trovata!")
        print("Assicurati di avere cartelle con file CSV nella directory corrente.\n")
        return
    
    print(f"\n📁 Trovate {len(event_folders)} cartelle evento:")
    for folder in event_folders:
        print(f"   - {folder.name}")
    
    print("\n" + "-" * 70)
    
    # Analizza ogni evento
    all_events_data = []
    
    for i, folder in enumerate(event_folders, 1):
        print(f"\n[{i}/{len(event_folders)}] Analisi evento: {folder.name}")
        print("-" * 70)
        
        try:
            analyzer = EventAnalyzer(str(folder))
            event_data = analyzer.analyze()
            analyzer.save_to_json(event_data)
            
            all_events_data.append(event_data)
            print(f"✅ {folder.name} analizzato con successo!")
            
        except Exception as e:
            print(f"❌ Errore nell'analisi di {folder.name}: {e}")
            continue
    
    # Genera l'indice per la dashboard
    if all_events_data:
        index_data = {
            'events': all_events_data,
            'total_events': len(all_events_data),
            'generated_at': all_events_data[0]['analysis_date'] if all_events_data else None
        }
        
        index_file = Path('events_index.json')
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 70)
        print(f"✅ ANALISI COMPLETATA!")
        print(f"📊 {len(all_events_data)} eventi analizzati con successo")
        print(f"💾 Indice salvato in: {index_file}")
        
        # Genera la dashboard HTML
        print("\n🔨 Generazione dashboard HTML...")
        try:
            from generate_dashboard import generate_dashboard
            generate_dashboard()
        except Exception as e:
            print(f"⚠️  Errore nella generazione dashboard: {e}")
            print("Puoi generarla manualmente con: python generate_dashboard.py")
        
        print("\n🌐 Apri index.html nel browser per visualizzare la dashboard")
        print("=" * 70 + "\n")
    else:
        print("\n⚠️  Nessun evento è stato analizzato con successo.\n")


if __name__ == '__main__':
    analyze_all_events()

