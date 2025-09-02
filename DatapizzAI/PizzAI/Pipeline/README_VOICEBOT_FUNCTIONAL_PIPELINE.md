# Voicebot con FunctionalPipeline

Questo README presenta una versione snella ma completa del voicebot basato su `FunctionalPipeline` (datapizzai). È focalizzato su un flusso pronto all’uso e mette in evidenza, con esempi concreti, le funzionalità del framework.

## Perché è utile

- Registri audio in locale e ottieni trascrizione, riassunto, riscrittura e sentiment con Gemini 2.5 Flash.
- Pipeline dichiarativa e componibile con `run`, `then`, `foreach`, `branch` e sottopipeline.
- Output in Markdown pronto per reportistica e con fallback robusto ai formati.

## Diagramma della pipeline

Se il rendering Mermaid non funziona nel tuo IDE, usa il diagramma ASCII sotto. Manteniamo anche il blocco Mermaid (per GitHub e viewer compatibili).

ASCII (fallback)

```
┌──────────────┐     ┌───────────────────────┐     ┌──────────────┐     ┌──────────────────────┐
│ RecordAudio  │ ─→  │ GeminiAudioAnalyzer   │ ─→  │ ExtractKey   │ ─→  │ Foreach: Normalize   │
│ (mic → .wav) │     │ (ASR+bullets+sentim.) │     │ (bullets[])  │     │ BulletPointNormalizer│
└──────────────┘     └───────────────────────┘     └──────────────┘     └─────────┬────────────┘
                                                                              ┌───▼───────────────┐
                                                                              │ Branch sentiment  │
                                                                              │ angry ?           │
                                                                              └───┬───────────┬───┘
                                                                                  │           │
                                                                                  │           │
                                                                      ┌───────────▼──┐   ┌────▼───────────┐
                                                                      │ SendNotification│ │ BuildReport MD │
                                                                      └────────────────┘ └────────────────┘
```

Mermaid (opzionale)

```mermaid
flowchart LR
  A[🎙️ RecordAudio] --> B[🧠 GeminiAudioAnalyzer\nASR + bullets + sentiment]
  B --> C[🧩 ExtractKey\n(bullets)]
  C --> D{{foreach\nBulletPointNormalizer}}
  B -->|sentiment: angry| E[⚠️ SendNotification]
  D --> F[📝 BuildReport (Markdown)]
```

Suggerimenti se Mermaid non rende: in VS Code installa "Markdown Preview Mermaid Support" oppure apri il file su GitHub.

## Quickstart

- Requisiti Python
  - `pip install datapizzai sounddevice soundfile python-dotenv pyyaml`
  - Linux: `sudo apt-get install -y portaudio19-dev` (per `sounddevice`)
- Credenziali
  - Crea `.env` nella root con: `GOOGLE_API_KEY=la_tua_api_key`

Esegui la versione semplice e funzionante:

```bash
python Pipeline/voicebot_with_datapizzai.py \
  --config Pipeline/voicebot_functional_pipeline.yaml
```

File di riferimento:
- Codice principale: `Pipeline/voicebot_with_datapizzai.py:56`
- Componenti: `Pipeline/components.py:16` `Pipeline/components.py:35` `Pipeline/components.py:129` `Pipeline/components.py:166` `Pipeline/components.py:194` `Pipeline/components.py:249`
- Config: `Pipeline/voicebot_functional_pipeline.yaml:1`

## Come funziona (in 5 step)

1. Record: registra audio mono 16 kHz e salva path.
2. Analyze: manda `.wav` a Gemini 2.5 Flash → trascrizione, bullets, riscrittura, sentiment.
3. Extract: isola i `bullets` dal risultato.
4. Foreach: normalizza ogni bullet in forma coerente.
5. Branch: se sentiment è `angry` invia notifica, altrimenti genera report Markdown.

Output: percorso del report MD (es. `Pipeline/voicebot_report.md`) e dizionario completo dei risultati.

## Le funzionalità del framework (con esempi reali)

- run: esegue un nodo e salva il risultato nel contesto
  - Esempio: `run(name="record", node=RecordAudio(), kwargs={...})` in `Pipeline/voicebot_with_datapizzai.py:81`
- then: concatena un nodo, con `dependencies` e `target_key` per dire quale output usare
  - Esempio: `then(name="analyze", ...)` con `target_key="audio_path"` in `Pipeline/voicebot_with_datapizzai.py:86`
- foreach: itera su una lista prodotta da un nodo precedente e applica un componente
  - Esempio: normalizzazione bullets in `Pipeline/voicebot_with_datapizzai.py:64`
- branch: biforca l’esecuzione su condizione (lambda sul contesto) verso sottopipeline
  - Esempio: controllo sentiment in `Pipeline/voicebot_with_datapizzai.py:97`
- Sub‑pipeline: componi blocchi riutilizzabili (notifica / normalizza+report)
  - Esempio: definizione di `notify` e `normalize_and_report` in `Pipeline/voicebot_with_datapizzai.py:61` e `Pipeline/voicebot_with_datapizzai.py:64`
- Componenti riusabili: ogni step è un `PipelineComponent` (sincrono/asincrono)
  - `RecordAudio` salva `{"audio_path": path}` `Pipeline/components.py:16`
  - `GeminiAudioAnalyzer` costruisce `report_markdown` robusto `Pipeline/components.py:35`
  - `ExtractKey("bullets")` estrae liste in modo tollerante `Pipeline/components.py:129`
  - `BulletPointNormalizer` normalizza e capitalizza `Pipeline/components.py:166`
  - `BuildReport` scrive su disco, sostituendo i bullets se normalizzati `Pipeline/components.py:194`
  - `SendNotification` mostra come integrare canali esterni `Pipeline/components.py:249`

## Esecuzione e parametri

- Comando tipico
  - `python Pipeline/voicebot_with_datapizzai.py --config Pipeline/voicebot_functional_pipeline.yaml`
- Override rapidi (CLI → YAML → default)
  - `--sec 30` durata registrazione
  - `--sr 16000` sample rate
  - `--audio session.wav` percorso audio
  - `--out Pipeline/voicebot_report.md` report MD
  - `--model gemini-2.5-flash` modello

## Output atteso

- Report Markdown con sezioni
  - Trascrizione
  - Riassunto (bullet normalizzati)
  - Riscrittura
  - Footer con sentiment, file e timestamp
- Esempio file: `Pipeline/voicebot_report.md`

## FAQ / Troubleshooting

- GOOGLE_API_KEY mancante
  - Aggiungi `.env` con `GOOGLE_API_KEY=...` e riapri il terminale.
- sounddevice non trovato / PortAudio
  - `pip install sounddevice soundfile` e su Linux installa `portaudio19-dev`.
- Nessun audio registrato
  - Verifica permessi microfono e dispositivo corretto.
- Mermaid non rende
  - Usa il diagramma ASCII oppure abilita un viewer compatibile.

## Estensioni rapide (idee)

- Aggiungi `SentimentChecker` per condizioni più ricche (`Pipeline/components.py:272`).
- Ramifica su sentiment multipli (positive/neutral/angry) usando sottopipeline diverse.
- Sposta i parametri variabili (durata, modello, output) nel tuo YAML e versionali.
