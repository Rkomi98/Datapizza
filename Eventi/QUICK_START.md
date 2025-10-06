# Quick start

## Setup rapido (5 minuti)

### 1. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 2. Configura OpenAI (opzionale)

Copia e modifica il file `.env`:

```bash
cp .env.example .env
# Modifica .env e inserisci la tua OPENAI_API_KEY
```

**Nota:** se non configuri l'API key, l'analisi funzionerà comunque ma senza analisi qualitativa GPT dei feedback testuali.

### 3. Analizza gli eventi

```bash
python analyze_all_events.py
```

Questo comando genera automaticamente:
- `analysis.json` per ogni evento
- `events_index.json` con l'indice globale
- `index.html` con la dashboard completa

### 4. Visualizza la dashboard

Apri `index.html` nel browser:

```bash
xdg-open index.html  # Linux
open index.html      # macOS
start index.html     # Windows
```

## Workflow per nuovi eventi

1. **Crea cartella evento** con nome descrittivo (es: `AperipizzaAI1125`)

2. **Aggiungi file CSV**:
   - File di profilazione partecipanti
   - File di feedback (opzionale)

3. **Esegui analisi**:
   ```bash
   python analyze_all_events.py
   ```

4. **(Opzionale) Crea report HTML personalizzato** usando come template `AperipizzaAI0925/index.html`

5. **Ricarica la dashboard** - si aggiornerà automaticamente

## Esempio di struttura cartella evento

```
NomeEvento1025/
├── responses.csv          # Dati profilazione
├── responses(1).csv       # Dati feedback
├── index.html            # Report HTML (opzionale, manuale)
└── analysis.json         # Generato automaticamente
```

## File generati automaticamente

- `analysis.json` - Tutti i dati analizzati per ogni evento
- `events_index.json` - Indice globale per la dashboard
- `kpi_extracted.json` - KPI estratti da HTML (se usi lo script di estrazione)

## Comandi principali

| Comando | Descrizione |
|---------|-------------|
| `python analyze_all_events.py` | Analizza tutti gli eventi |
| `python analyze_event.py <folder>` | Analizza un singolo evento |
| `python extract_kpi_from_html.py <file.html>` | Estrae KPI da HTML esistente |

## Troubleshooting rapido

**Dashboard vuota o errore "Impossibile caricare i dati"?**
→ Esegui `python analyze_all_events.py` o `python generate_dashboard.py`

**Errore encoding CSV?**
→ Salva il CSV come UTF-8

**Analisi GPT non funziona?**
→ Verifica il file `.env` e la API key OpenAI

**KPI non accurati?**
→ Verifica che i nomi delle colonne nei CSV siano standard (es: "Job Title", "Azienda", "Valutazione")

## Documentazione completa

Leggi `README.md` per la documentazione completa del progetto.

