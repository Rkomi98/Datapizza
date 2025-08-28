# Voicebot con FunctionalPipeline

## 1. Panoramica

Questo sistema implementa un voicebot per l'analisi vocale utilizzando il `FunctionalPipeline` di datapizzai. La pipeline registra audio, lo analizza tramite Gemini 2.5 Flash, e genera report automatici con gestione intelligente del sentiment.

### Caratteristiche principali

- Registrazione audio in tempo reale
- Analisi automatica con trascrizione, riassunto e sentiment
- Pipeline modulare con branch condizionali  
- Notifiche automatiche per utenti arrabbiati
- Report markdown strutturati
- Configurazione tramite YAML

## 2. Architettura della pipeline

### Componenti utilizzati

La pipeline utilizza i seguenti `PipelineComponent`:

- `RecordAudio`: registrazione audio mono PCM16
- `GeminiAudioAnalyzer`: analisi completa con Gemini 2.5 Flash
- `ExtractKey`: estrazione dati specifici dai risultati
- `BulletPointNormalizer`: normalizzazione bullet points
- `BuildReport`: generazione report markdown
- `SendNotification`: invio notifiche per sentiment negativi

### Flusso della pipeline

1. **Registrazione**: cattura audio per durata specificata
2. **Analisi**: trascrizione, riassunto e sentiment analysis
3. **Estrazione**: isolamento bullet points dal risultato
4. **Normalizzazione**: standardizzazione formato bullet points (foreach)
5. **Branch condizionale**: gestione basata su sentiment
   - Se arrabbiato: invio notifica
   - Se normale: generazione report
6. **Output**: risultato finale strutturato

## 3. Installazione e configurazione

### Requisiti di sistema

```bash
pip install sounddevice soundfile python-dotenv pyyaml
```

### Configurazione ambiente

Creare file `.env` nella root del progetto:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

### Configurazione YAML

Il file `voicebot_functional_pipeline.yaml` contiene i parametri di configurazione:

```yaml
params:
  seconds: 20
  sample_rate: 16000
  audio_path: "session.wav"
  out_path: "Pipeline/voicebot_report.md"
  model: "gemini-2.5-flash"
  temperature: 0.4

modules:
  - name: data_recorder
    module: Pipeline.components
    type: RecordAudio
    params: {}

  - name: audio_analyzer
    module: Pipeline.components
    type: GeminiAudioAnalyzer
    params:
      model: "gemini-2.5-flash"
      temperature: 0.4
```

## 4. Utilizzo

### Esecuzione base

```bash
python Pipeline/voicebot_functional_complete.py --mode basic
```

### Esecuzione con configurazione personalizzata

```bash
python Pipeline/voicebot_functional_complete.py \
    --config Pipeline/voicebot_functional_pipeline.yaml \
    --mode yaml \
    --sec 30 \
    --out custom_report.md
```

### Modalità disponibili

- `basic`: pipeline programmatica standard
- `yaml`: caricamento da configurazione YAML  
- `advanced`: pipeline con pattern complessi e branch multipli

### Parametri CLI

| Parametro | Descrizione | Default |
|-----------|-------------|---------|
| `--config` | File YAML di configurazione | `voicebot_functional_pipeline.yaml` |
| `--mode` | Modalità pipeline | `basic` |
| `--sec` | Durata registrazione (secondi) | `20` |
| `--sr` | Sample rate | `16000` |
| `--audio` | Percorso file audio | `session.wav` |
| `--out` | Percorso report output | `Pipeline/voicebot_report.md` |
| `--model` | Modello Gemini | `gemini-2.5-flash` |

## 5. Esempi di codice

### Pipeline programmatica base

```python
from datapizzai.pipeline import Dependency, FunctionalPipeline
from Pipeline.components import *

# Inizializzazione componenti
recorder = RecordAudio()
analyzer = GeminiAudioAnalyzer(api_key=GOOGLE_API_KEY)
normalizer = BulletPointNormalizer()

# Sottopipeline per notifiche
notification_pipeline = (
    FunctionalPipeline()
    .run(name="send_notification", node=SendNotification())
)

# Pipeline principale con branch
pipeline = (
    FunctionalPipeline()
    .run(name="record", node=recorder, kwargs={"seconds": 20})
    .then(name="analyze", node=analyzer, target_key="audio_path")
    .then(name="extract", node=ExtractKey(key="bullets"), target_key="analyze")
    .foreach(name="normalize", dependencies=[Dependency(node_name="extract")], do=normalizer)
    .branch(
        condition=lambda ctx: ctx.get("analyze", {}).get("sentiment") == "angry",
        dependencies=[Dependency(node_name="analyze")],
        if_true=notification_pipeline,
        if_false=report_pipeline
    )
)

# Esecuzione
results = pipeline.execute()
```

### Utilizzo di foreach per normalizzazione

```python
# Foreach per processare lista di bullet points
normalize_pipeline = (
    FunctionalPipeline()
    .foreach(
        name="normalize_bullets",
        dependencies=[Dependency(node_name="extract_bullets")],
        do=BulletPointNormalizer(),
    )
)
```

### Branch condizionale per sentiment

```python
# Branch basato su sentiment analysis
sentiment_branch = pipeline.branch(
    condition=lambda ctx: (
        ctx.get("analyze_audio", {})
        .get("sentiment", "").lower() in ["angry", "furious"]
    ),
    dependencies=[Dependency(node_name="analyze_audio")],
    if_true=notification_pipeline,
    if_false=report_pipeline,
)
```

## 6. Struttura output

### Report markdown generato

```markdown
## Trascrizione
[Testo trascritto dall'audio]

## Riassunto (bullet)
- Punto principale 1
- Punto principale 2
- Punto principale 3

## Riscrittura
[Versione rielaborata del contenuto]

_Sentiment_: neutral | _File_: session.wav | _Ts_: 2024-01-15 14:30:00
```

### Risultati pipeline

La chiamata `pipeline.execute()` restituisce un dizionario con:

```python
{
    "record_audio": {"audio_path": "session.wav"},
    "analyze_audio": {
        "transcript": "...",
        "bullets": ["...", "..."],
        "rewrite": "...",
        "sentiment": "neutral",
        "report_markdown": "..."
    },
    "extract_bullets": ["...", "..."],
    "normalize_bullets": ["- Punto 1", "- Punto 2"],
    "generate_report": "Pipeline/voicebot_report.md"
}
```

## 7. Personalizzazione e estensione

### Creazione di componenti personalizzati

```python
from datapizzai.core.models import PipelineComponent

class CustomAnalyzer(PipelineComponent):
    def _run(self, data):
        # Logica di analisi personalizzata
        return processed_data
    
    async def _a_run(self, data):
        # Versione asincrona
        return processed_data
```

### Aggiunta di nuove condizioni branch

```python
# Condizioni personalizzate per branch
custom_condition = lambda ctx: (
    len(ctx.get("transcript", "")) > 500 and
    "urgente" in ctx.get("transcript", "").lower()
)

pipeline.branch(
    condition=custom_condition,
    if_true=urgent_pipeline,
    if_false=normal_pipeline
)
```

### Pattern foreach avanzati

```python
# Foreach con dipendenze multiple
advanced_foreach = (
    FunctionalPipeline()
    .foreach(
        name="process_items",
        dependencies=[
            Dependency(node_name="source_data"),
            Dependency(node_name="config_data", target_key="config")
        ],
        do=CustomProcessor(),
    )
)
```

## 8. Risoluzione problemi

### Errori comuni

**Errore: GOOGLE_API_KEY mancante**
- Verificare la presenza del file `.env`
- Controllare che la chiave sia valida e attiva

**Errore: Modulo sounddevice non trovato**
- Installare dipendenze: `pip install sounddevice soundfile`
- Su Linux: `sudo apt-get install portaudio19-dev`

**Errore: Pipeline execution failed**
- Verificare che tutti i componenti siano correttamente inizializzati
- Controllare i log per errori specifici dei componenti

### Debug della pipeline

```python
# Attivazione logging dettagliato
import logging
logging.basicConfig(level=logging.DEBUG)

# Stampa stato pipeline
results = pipeline.execute()
print("Keys disponibili:", list(results.keys()))
for key, value in results.items():
    print(f"{key}: {type(value)}")
```

## 9. Best practices

### Gestione errori

- Implementare validation nei componenti personalizzati
- Utilizzare try/catch nei metodi `_run()`
- Verificare dipendenze prima dell'esecuzione

### Performance

- Utilizzare componenti asincroni quando possibile
- Configurare timeout appropriati per registrazione audio
- Ottimizzare prompt per Gemini per ridurre latenza

### Manutenibilità

- Separare logica di business dai componenti pipeline
- Utilizzare configurazione YAML per parametri variabili
- Documentare condizioni branch e dipendenze complesse
