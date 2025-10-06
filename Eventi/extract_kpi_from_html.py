#!/usr/bin/env python3
"""
Script per estrarre KPI da file HTML esistenti.
Utile per eventi già documentati senza CSV disponibili.
"""

import re
import json
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional


class HTMLKPIExtractor:
    """Estrae KPI da file HTML esistenti."""
    
    def __init__(self, html_file: str):
        self.html_file = Path(html_file)
        self.event_folder = self.html_file.parent
        self.event_name = self.event_folder.name
        
        with open(self.html_file, 'r', encoding='utf-8') as f:
            self.soup = BeautifulSoup(f.read(), 'html.parser')
    
    def extract_metric_cards(self) -> Dict[str, Any]:
        """Estrae i dati dalle metric cards."""
        metrics = {}
        
        # Cerca tutte le metric cards
        metric_cards = self.soup.find_all('div', class_='metric-card')
        
        for card in metric_cards:
            value_elem = card.find('span', class_='metric-value')
            label_elem = card.find('span', class_='metric-label')
            
            if value_elem and label_elem:
                label = label_elem.text.strip()
                value = value_elem.text.strip()
                
                # Converti il valore in numero se possibile
                try:
                    if '%' in value:
                        value = float(value.replace('%', ''))
                    else:
                        value = int(value)
                except ValueError:
                    pass  # Mantieni come stringa
                
                metrics[label] = value
        
        return metrics
    
    def extract_title(self) -> str:
        """Estrae il titolo dell'evento."""
        h1 = self.soup.find('h1')
        return h1.text.strip() if h1 else self.event_name
    
    def extract_insights(self) -> list:
        """Estrae gli insights dall'HTML."""
        insights = []
        
        insight_cards = self.soup.find_all('div', class_='insight-card')
        
        for card in insight_cards:
            title_elem = card.find('h3', class_='insight-title')
            text_elem = card.find('p', class_='insight-text')
            
            if title_elem and text_elem:
                insights.append({
                    'title': title_elem.text.strip(),
                    'text': text_elem.text.strip()
                })
        
        return insights
    
    def extract_companies(self) -> list:
        """Estrae la lista delle aziende."""
        companies = []
        
        company_tags = self.soup.find_all('div', class_='company-tag')
        
        for tag in company_tags:
            company = tag.text.strip()
            if company:
                companies.append(company)
        
        return companies
    
    def extract_all(self) -> Dict[str, Any]:
        """Estrae tutti i KPI disponibili."""
        return {
            'event_name': self.event_name,
            'event_folder': str(self.event_folder),
            'title': self.extract_title(),
            'metrics': self.extract_metric_cards(),
            'insights': self.extract_insights(),
            'companies': self.extract_companies(),
            'source': 'html_extraction'
        }
    
    def save_to_json(self, output_file: Optional[Path] = None):
        """Salva i KPI estratti in JSON."""
        if output_file is None:
            output_file = self.event_folder / 'kpi_extracted.json'
        
        data = self.extract_all()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ KPI estratti salvati in: {output_file}")
        return data


def main():
    """Main function."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extract_kpi_from_html.py <html_file>")
        print("\nEsempio: python extract_kpi_from_html.py AperipizzaAI0925/index.html")
        sys.exit(1)
    
    html_file = sys.argv[1]
    
    if not Path(html_file).exists():
        print(f"❌ File non trovato: {html_file}")
        sys.exit(1)
    
    print(f"\n📄 Estrazione KPI da: {html_file}")
    print("=" * 60)
    
    extractor = HTMLKPIExtractor(html_file)
    data = extractor.save_to_json()
    
    print("\n📊 KPI estratti:")
    print("-" * 60)
    for key, value in data['metrics'].items():
        print(f"  {key}: {value}")
    
    print(f"\n💼 Aziende trovate: {len(data['companies'])}")
    print(f"📝 Insights trovati: {len(data['insights'])}")


if __name__ == '__main__':
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("❌ BeautifulSoup4 non installato!")
        print("\nInstalla con: pip install beautifulsoup4")
        exit(1)
    
    main()

