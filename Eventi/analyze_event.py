#!/usr/bin/env python3
"""
Script per analizzare i dati degli eventi Datapizza e generare KPI automaticamente.
Analizza i CSV di profilazione e feedback, usa GPT per analisi qualitative.
"""

import os
import sys
import json
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()


class EventAnalyzer:
    """Analizzatore dati evento."""
    
    def __init__(self, event_folder: str):
        self.event_folder = Path(event_folder)
        self.event_name = self.event_folder.name
        self.openai_client = None
        
        # Inizializza OpenAI se disponibile
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=api_key)
            except ImportError:
                print("⚠️ Libreria OpenAI non installata. Installa con: pip install openai")
            except Exception as e:
                print(f"⚠️ Errore inizializzazione OpenAI: {e}")
        else:
            print("⚠️ OPENAI_API_KEY non trovata nel file .env. L'analisi qualitativa sarà limitata.")
    
    def find_csv_files(self) -> Dict[str, Optional[Path]]:
        """Trova i file CSV nella cartella evento."""
        csv_files = list(self.event_folder.glob('*.csv'))
        
        result = {
            'profiling': None,
            'feedback': None,
            'registrations': None
        }
        
        for csv_file in csv_files:
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    header = f.readline().lower()
                    
                    # Identifica tipo di file in ordine di specificità
                    if ('registrat' in header or 'iscritt' in header) and 'status' in header:
                        result['registrations'] = csv_file
                    elif 'nato/a' in header or 'job title' in header or 'azienda' in header:
                        result['profiling'] = csv_file
                    elif 'valuteresti' in header or 'feedback' in header or 'suggerimenti' in header:
                        result['feedback'] = csv_file
            except Exception:
                continue
        
        return result
    
    def read_csv_safe(self, filepath: Path) -> List[Dict[str, Any]]:
        """Legge un CSV gestendo vari encoding e formati."""
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    return [row for row in reader]
            except (UnicodeDecodeError, Exception) as e:
                continue
        
        print(f"❌ Impossibile leggere {filepath}")
        return []
    
    def extract_number_from_stars(self, stars: str) -> int:
        """Estrae il numero di stelle da una stringa, validando che sia tra 1 e 5."""
        if not stars:
            return 0
        
        stars_str = str(stars)
        
        # Conta le stelle emoji (due varianti: ⭐ e ⭐️)
        stars_count = stars_str.count('⭐')
        if stars_count > 0 and 1 <= stars_count <= 5:
            return stars_count
        
        # Prova a estrarre numeri dalla stringa
        numbers = re.findall(r'\d+', stars_str)
        if numbers:
            num = int(numbers[0])
            # Valida che sia un rating sensato (1-5)
            if 1 <= num <= 5:
                return num
        
        return 0
    
    def analyze_registration_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizza i dati di registrazione (iscrizioni)."""
        if not data:
            return {}
        
        # Trova il campo status
        status_field = self._find_field(data[0], ['status', 'stato', 'registration'])
        if not status_field:
            print("⚠️  Campo 'Status' non trovato nel file di registrazione.")
            return {}
        
        # Analizza gli status
        statuses = [str(row.get(status_field, '')).lower().strip() for row in data]
        
        iscritti_iniziali = len(statuses)
        disiscritti = sum(1 for s in statuses if 'disiscritt' in s or 'unsubscribe' in s)
        partecipanti = sum(1 for s in statuses if 'partecipant' in s or 'attended' in s or 'presente' in s)
        iscritti_finali = iscritti_iniziali - disiscritti
        
        # Calcola tassi
        tasso_presenza = round(partecipanti / iscritti_finali * 100, 1) if iscritti_finali > 0 else 0
        tasso_no_show = round(100 - tasso_presenza, 1) if iscritti_finali > 0 else 0
        
        return {
            'iscritti_iniziali': iscritti_iniziali,
            'disiscritti': disiscritti,
            'iscritti_finali': iscritti_finali,
            'partecipanti': partecipanti,
            'tasso_presenza': tasso_presenza,
            'tasso_no_show': tasso_no_show
        }
    
    def analyze_profiling_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizza i dati di profilazione."""
        if not data:
            return {}
        
        total = len(data)
        
        # Analizza età
        birth_years = []
        for row in data:
            year_field = self._find_field(row, ['anno', 'nato', 'birth'])
            if year_field and row[year_field]:
                year_str = str(row[year_field])
                # Estrai anno (può essere YYYY o DD/MM/YYYY)
                year_match = re.search(r'(\d{4})', year_str)
                if year_match:
                    year = int(year_match.group(1))
                    if 1940 <= year <= 2010:
                        birth_years.append(year)
        
        ages = [2025 - year for year in birth_years]
        age_ranges = {
            '<25': sum(1 for age in ages if age < 25),
            '25-34': sum(1 for age in ages if 25 <= age <= 34),
            '35-44': sum(1 for age in ages if 35 <= age <= 44),
            '45+': sum(1 for age in ages if age >= 45)
        }
        
        # Analizza studenti vs professionisti
        status_field = self._find_field(row, ['nella vita', 'status', 'occupation'])
        students = sum(1 for row in data if 'stud' in str(row.get(status_field, '')).lower())
        professionals = total - students
        
        # Analizza esperienza lavorativa
        exp_field = self._find_field(data[0], ['esperienza', 'experience', 'anni'])
        experience_levels = Counter()
        for row in data:
            if exp_field and row[exp_field]:
                exp = str(row[exp_field]).lower()
                if 'meno' in exp or '<' in exp or 'less' in exp:
                    experience_levels['<1'] += 1
                elif '1-3' in exp or '1-2' in exp:
                    experience_levels['1-3'] += 1
                elif '3-5' in exp or '4-5' in exp:
                    experience_levels['3-5'] += 1
                elif '5+' in exp or '>5' in exp or 'senior' in exp:
                    experience_levels['5+'] += 1
        
        # Analizza job titles e categorizza
        job_field = self._find_field(data[0], ['job title', 'title', 'ruolo', 'lavoro'])
        jobs = [str(row.get(job_field, '')).strip() for row in data if row.get(job_field) and str(row.get(job_field, '')).strip()]
        jobs_lower = [j.lower() for j in jobs]
        
        categories = self._categorize_jobs(jobs_lower)
        
        # Analizza aziende
        company_field = self._find_field(data[0], ['azienda', 'company', 'lavori'])
        companies = [str(row.get(company_field, '')).strip() for row in data 
                    if row.get(company_field) and str(row.get(company_field)).strip()]
        companies = [c for c in companies if c and c.lower() not in ['', 'nan', 'none']]
        unique_companies = list(set(companies))
        
        # Analizza motivazioni partecipazione
        motivation_field = self._find_field(data[0], ['motivo', 'motivation', 'principale'])
        motivations = Counter()
        for row in data:
            if motivation_field and row[motivation_field]:
                mot = str(row[motivation_field]).strip()
                if mot:
                    motivations[mot] += 1
        
        # Analizza interessi futuri
        interest_field = self._find_field(data[0], ['interesse', 'partecipare', 'future'])
        future_participation = Counter()
        for row in data:
            if interest_field and row[interest_field]:
                answer = str(row[interest_field]).strip().lower()
                if 'sì' in answer or 'si' in answer or 'yes' in answer:
                    future_participation['Sì'] += 1
                elif 'no' in answer:
                    future_participation['No'] += 1
                elif 'forse' in answer or 'maybe' in answer:
                    future_participation['Forse'] += 1
        
        # Analizza topic di interesse
        topic_field = self._find_field(data[0], ['tema', 'topic', 'approfondire'])
        topics = []
        for row in data:
            if topic_field and row[topic_field]:
                topic = str(row[topic_field]).strip()
                if topic and topic.lower() not in ['', 'nan', 'none', 'no']:
                    topics.append(topic)
        
        return {
            'total_responses': total,
            'age_distribution': age_ranges,
            'students_vs_professionals': {
                'students': students,
                'professionals': professionals,
                'students_percentage': round(students / total * 100, 1) if total > 0 else 0,
                'professionals_percentage': round(professionals / total * 100, 1) if total > 0 else 0
            },
            'experience_levels': dict(experience_levels),
            'job_categories': categories,
            'companies': {
                'total_unique': len(unique_companies),
                'list': sorted(unique_companies)
            },
            'motivations': dict(motivations),
            'future_participation': dict(future_participation),
            'topics_of_interest': topics
        }
    
    def _categorize_jobs(self, jobs: List[str]) -> Dict[str, Any]:
        """Categorizza i job title in macro-categorie."""
        categories = {
            'Data & AI': {
                'keywords': ['data', 'scientist', 'analyst', 'ml', 'machine learning', 'ai', 'artificial intelligence', 'nlp'],
                'count': 0,
                'jobs': []
            },
            'Management & Leadership': {
                'keywords': ['ceo', 'founder', 'manager', 'head', 'director', 'lead', 'product manager', 'pmo'],
                'count': 0,
                'jobs': []
            },
            'Software & Engineering': {
                'keywords': ['software', 'developer', 'engineer', 'architect', 'fullstack', 'backend', 'frontend'],
                'count': 0,
                'jobs': []
            },
            'Marketing & Growth': {
                'keywords': ['marketing', 'growth', 'communication', 'copywriter', 'sales'],
                'count': 0,
                'jobs': []
            },
            'Other': {
                'keywords': [],
                'count': 0,
                'jobs': []
            }
        }
        
        for job in jobs:
            categorized = False
            for category, info in categories.items():
                if category == 'Other':
                    continue
                if any(keyword in job.lower() for keyword in info['keywords']):
                    info['count'] += 1
                    info['jobs'].append(job)
                    categorized = True
                    break
            
            if not categorized:
                categories['Other']['count'] += 1
                categories['Other']['jobs'].append(job)
        
        # Calcola percentuali
        total = len(jobs)
        for category, info in categories.items():
            info['percentage'] = round(info['count'] / total * 100, 1) if total > 0 else 0
        
        return categories
    
    def analyze_feedback_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizza i dati di feedback."""
        if not data:
            return {}
        
        total = len(data)
        
        # Trova campi ratings (usa keywords più specifiche)
        overall_field = self._find_field(data[0], ['valuteresti complessivamente', 'overall', 'complessivamente'])
        networking_field = self._find_field(data[0], ['valuteresti networking', 'networking', 'aperitivo'])
        
        # Analizza ratings
        overall_ratings = []
        networking_ratings = []
        
        for row in data:
            if overall_field and row[overall_field]:
                rating = self.extract_number_from_stars(row[overall_field])
                if rating > 0:
                    overall_ratings.append(rating)
            
            if networking_field and row[networking_field]:
                rating = self.extract_number_from_stars(row[networking_field])
                if rating > 0:
                    networking_ratings.append(rating)
        
        # Calcola distribuzioni
        overall_distribution = Counter(overall_ratings)
        networking_distribution = Counter(networking_ratings)
        
        # Analizza suggerimenti testuali
        suggestions_field = self._find_field(data[0], ['suggerimenti', 'migliorare', 'suggestions'])
        suggestions = []
        for row in data:
            if suggestions_field and row[suggestions_field]:
                text = str(row[suggestions_field]).strip()
                if text and len(text) > 10:  # Ignora risposte troppo brevi
                    suggestions.append(text)
        
        # Analizza interesse futuro
        future_field = self._find_field(data[0], ['futuro', 'future', 'partecipare'])
        future_interest = Counter()
        for row in data:
            if future_field and row[future_field]:
                answer = str(row[future_field]).strip()
                if answer:
                    future_interest[answer] += 1
        
        return {
            'total_responses': total,
            'overall_rating': {
                'average': round(sum(overall_ratings) / len(overall_ratings), 2) if overall_ratings else 0,
                'distribution': dict(overall_distribution),
                'total_responses': len(overall_ratings)
            },
            'networking_rating': {
                'average': round(sum(networking_ratings) / len(networking_ratings), 2) if networking_ratings else 0,
                'distribution': dict(networking_distribution),
                'total_responses': len(networking_ratings)
            },
            'suggestions': suggestions,
            'future_interest': dict(future_interest)
        }
    
    def analyze_suggestions_with_gpt(self, suggestions: List[str]) -> Dict[str, Any]:
        """Analizza i suggerimenti testuali usando GPT."""
        if not self.openai_client or not suggestions:
            return {
                'summary': 'Analisi GPT non disponibile',
                'categories': {},
                'key_improvements': []
            }
        
        try:
            # Prepara il prompt
            suggestions_text = '\n'.join([f"- {s}" for s in suggestions])
            
            prompt = f"""Analizza i seguenti feedback di un evento tech sulla data science e AI:

{suggestions_text}

Fornisci:
1. Un breve sommario delle principali tematiche emerse (max 3 frasi)
2. Categorizza i feedback in macro-aree (es: networking, contenuti, logistica, catering)
3. Lista i 3-5 punti di miglioramento più ricorrenti

Rispondi in formato JSON con questa struttura:
{{
    "summary": "breve sommario",
    "categories": {{"categoria": ["feedback1", "feedback2"]}},
    "key_improvements": ["punto1", "punto2", "punto3"]
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Sei un analista esperto di feedback per eventi tech."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"⚠️ Errore nell'analisi GPT: {e}")
            return {
                'summary': 'Analisi non disponibile',
                'categories': {},
                'key_improvements': []
            }
    
    def _find_field(self, row: Dict[str, Any], keywords: List[str]) -> Optional[str]:
        """Trova un campo nel dizionario basandosi su keywords."""
        if not row:
            return None
        
        for key in row.keys():
            key_lower = key.lower()
            if any(keyword in key_lower for keyword in keywords):
                return key
        return None
    
    def analyze(self) -> Dict[str, Any]:
        """Esegue l'analisi completa dell'evento."""
        print(f"\n📊 Analisi evento: {self.event_name}")
        print("=" * 60)
        
        # Trova CSV
        csv_files = self.find_csv_files()
        
        result = {
            'event_name': self.event_name,
            'event_folder': str(self.event_folder),
            'analysis_date': datetime.now().isoformat(),
            'registration_data': {},
            'profiling_data': {},
            'feedback_data': {},
            'kpis': {}
        }
        
        # Analizza registrazioni
        if csv_files['registrations']:
            print(f"✓ Trovato file registrazioni: {csv_files['registrations'].name}")
            registration_data = self.read_csv_safe(csv_files['registrations'])
            result['registration_data'] = self.analyze_registration_data(registration_data)
            if result['registration_data']:
                print(f"  → {result['registration_data'].get('iscritti_iniziali', 0)} iscrizioni analizzate")
        else:
            print("ℹ️  File registrazioni non trovato (opzionale)")
        
        # Analizza profilazione
        if csv_files['profiling']:
            print(f"✓ Trovato file profilazione: {csv_files['profiling'].name}")
            profiling_data = self.read_csv_safe(csv_files['profiling'])
            result['profiling_data'] = self.analyze_profiling_data(profiling_data)
            print(f"  → {result['profiling_data'].get('total_responses', 0)} risposte analizzate")
        else:
            print("✗ File profilazione non trovato")
        
        # Analizza feedback
        if csv_files['feedback']:
            print(f"✓ Trovato file feedback: {csv_files['feedback'].name}")
            feedback_data = self.read_csv_safe(csv_files['feedback'])
            result['feedback_data'] = self.analyze_feedback_data(feedback_data)
            print(f"  → {result['feedback_data'].get('total_responses', 0)} feedback analizzati")
            
            # Analisi qualitativa con GPT
            if result['feedback_data'].get('suggestions'):
                print("🤖 Analisi qualitativa con GPT in corso...")
                gpt_analysis = self.analyze_suggestions_with_gpt(
                    result['feedback_data']['suggestions']
                )
                result['feedback_data']['gpt_analysis'] = gpt_analysis
                print("  → Analisi completata")
        else:
            print("✗ File feedback non trovato")
        
        # Calcola KPI aggregati
        result['kpis'] = self._calculate_kpis(result)
        
        print("\n✅ Analisi completata!\n")
        return result
    
    def _calculate_kpis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calcola KPI aggregati per l'evento."""
        kpis = {}
        
        prof = analysis.get('profiling_data', {})
        feed = analysis.get('feedback_data', {})
        reg = analysis.get('registration_data', {})
        
        # KPI da registrazioni (se disponibili)
        if reg:
            kpis['iscritti_iniziali'] = reg.get('iscritti_iniziali', 0)
            kpis['disiscritti'] = reg.get('disiscritti', 0)
            kpis['iscritti_finali'] = reg.get('iscritti_finali', 0)
            kpis['partecipanti'] = reg.get('partecipanti', 0)
            kpis['tasso_presenza'] = reg.get('tasso_presenza', 0)
            kpis['tasso_no_show'] = reg.get('tasso_no_show', 0)
        
        # KPI da profilazione e feedback
        kpis['profiling_responses'] = prof.get('total_responses', 0)
        kpis['feedback_responses'] = feed.get('total_responses', 0)
        
        # Feedback rate: usa partecipanti se disponibili, altrimenti profiling_responses
        base_for_feedback = kpis.get('partecipanti', 0) or kpis['profiling_responses']
        if base_for_feedback > 0:
            kpis['feedback_rate'] = round(
                kpis['feedback_responses'] / base_for_feedback * 100, 1
            )
        
        # KPI satisfaction
        if feed.get('overall_rating'):
            kpis['overall_satisfaction'] = feed['overall_rating']['average']
            dist = feed['overall_rating']['distribution']
            total_ratings = sum(dist.values())
            kpis['satisfaction_5_stars_percentage'] = round(
                dist.get(5, 0) / total_ratings * 100, 1
            ) if total_ratings > 0 else 0
        
        # KPI retention
        if feed.get('future_interest'):
            total_interest = sum(feed['future_interest'].values())
            yes_count = feed['future_interest'].get('Sì', 0) + feed['future_interest'].get('Si', 0)
            kpis['future_participation_rate'] = round(
                yes_count / total_interest * 100, 1
            ) if total_interest > 0 else 0
        
        # KPI diversità
        if prof.get('companies'):
            kpis['unique_companies'] = prof['companies']['total_unique']
        
        return kpis
    
    def save_to_json(self, data: Dict[str, Any], output_file: Optional[Path] = None):
        """Salva i risultati in JSON."""
        if output_file is None:
            output_file = self.event_folder / 'analysis.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Dati salvati in: {output_file}")
        
        # Genera la pagina HTML dell'evento
        try:
            from generate_event_page import generate_event_page
            generate_event_page(str(self.event_folder))
        except Exception as e:
            print(f"⚠️  Errore generazione pagina HTML: {e}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_event.py <event_folder>")
        print("\nEsempio: python analyze_event.py AperipizzaAI0925")
        sys.exit(1)
    
    event_folder = sys.argv[1]
    
    if not os.path.exists(event_folder):
        print(f"❌ Cartella non trovata: {event_folder}")
        sys.exit(1)
    
    analyzer = EventAnalyzer(event_folder)
    results = analyzer.analyze()
    analyzer.save_to_json(results)
    
    # Stampa KPI principali
    print("\n📈 KPI Principali:")
    print("-" * 60)
    for key, value in results['kpis'].items():
        print(f"  {key}: {value}")


if __name__ == '__main__':
    main()

