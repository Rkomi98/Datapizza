# Voicebot with FunctionalPipeline

This README presents a lean but complete voicebot based on `FunctionalPipeline` (datapizza-ai). It focuses on a ready‑to‑use flow and highlights, with concrete examples, the framework’s features.

## Why it’s useful

- Record audio locally and get transcription, summary, rewrite, and sentiment with Gemini 2.5 Flash.
- Declarative, composable pipeline with `run`, `then`, `foreach`, `branch`, and sub‑pipelines.
- Markdown output ready for reporting, with robust formatting fallbacks.

## Pipeline diagram

ASCII (fallback)

```
┌──────────────┐     ┌───────────────────────┐     ┌──────────────┐     ┌──────────────────────┐
│ RecordAudio  │ ─→  │ GeminiAudioAnalyzer   │ ─→  │ ExtractKey   │ ─→  │ Foreach: Normalize   │
│ (mic → .wav) │     │ (ASR+bullets+sentim.) │     │ (bullets[])  │     │ BulletPointNormalizer│
└──────────────┘     └───────────────────────┘     └──────────────┘     └─────────┬────────────┘
                                                                                  |
                                                                        ┌─────────▼─────────────┐
                                                                        │ Branch sentiment      │
                                                                        │ angry ?               │
                                                                        └───┬───────────────┬───┘
                                                                            │               │
                                                                            │               │
                                                                ┌───────────▼─────┐    ┌────▼───────────┐
                                                                │ SendNotification│    │ BuildReport MD │
                                                                └─────────────────┘    └────────────────┘
```

Mermaid (optional)

```mermaid
flowchart LR
  A[RecordAudio] --> B[GeminiAudioAnalyzer<br/>ASR + bullets + sentiment]
  B --> C[ExtractKey<br/>(bullets)]
  C --> D{{foreach<br/>BulletPointNormalizer}}
  B -->|sentiment: angry| E[SendNotification]
  D --> F[BuildReport (Markdown)]
```

## Quickstart

- Python requirements
  - `pip install datapizza-ai sounddevice soundfile python-dotenv pyyaml`
  - Linux: `sudo apt-get install -y portaudio19-dev` (for `sounddevice`)
- Credentials
  - Create `.env` at project root with: `GOOGLE_API_KEY=your_api_key`

Run the simple working version:

```bash
python Pipeline/voicebot_with_datapizza-ai.py \
  --config Pipeline/voicebot_functional_pipeline.yaml
```

Reference files:
- Main code: `Pipeline/voicebot_with_datapizza-ai.py:56`
- Components: `Pipeline/components.py:16` `Pipeline/components.py:35` `Pipeline/components.py:129` `Pipeline/components.py:166` `Pipeline/components.py:194` `Pipeline/components.py:249`
- Config: `Pipeline/voicebot_functional_pipeline.yaml:1`

## How it works (in 5 steps)

1. Record: capture mono 16 kHz audio and save path.
2. Analyze: send `.wav` to Gemini 2.5 Flash → transcription, bullets, rewrite, sentiment.
3. Extract: isolate `bullets` from the result.
4. Foreach: normalize each bullet into a consistent form.
5. Branch: if sentiment is `angry` send a notification, otherwise generate a Markdown report.

Output: path of the MD report (e.g., `Pipeline/voicebot_report.md`) and the full result dictionary.

## Framework features (with real examples)

- run: execute a node and save its result in the context
  - Example: `run(name="record", node=RecordAudio(), kwargs={...})` in `Pipeline/voicebot_with_datapizza-ai.py:81`
- then: chain a node, with `dependencies` and `target_key` to specify which output to use
  - Example: `then(name="analyze", ...)` with `target_key="audio_path"` in `Pipeline/voicebot_with_datapizza-ai.py:86`
- foreach: iterate over a list produced by a previous node and apply a component
  - Example: bullet normalization in `Pipeline/voicebot_with_datapizza-ai.py:64`
- branch: split execution on a condition (lambda on the context) to sub‑pipelines
  - Example: sentiment check in `Pipeline/voicebot_with_datapizza-ai.py:97`
- Sub‑pipeline: compose reusable blocks (notification / normalize+report)
  - Example: definition of `notify` and `normalize_and_report` in `Pipeline/voicebot_with_datapizza-ai.py:61` and `Pipeline/voicebot_with_datapizza-ai.py:64`
- Reusable components: each step is a `PipelineComponent` (sync/async)
  - `RecordAudio` saves `{ "audio_path": path }` `Pipeline/components.py:16`
  - `GeminiAudioAnalyzer` constructs a robust `report_markdown` `Pipeline/components.py:35`
  - `ExtractKey("bullets")` extracts lists tolerantly `Pipeline/components.py:129`
  - `BulletPointNormalizer` normalizes and capitalizes `Pipeline/components.py:166`
  - `BuildReport` writes to disk, replacing bullets if normalized `Pipeline/components.py:194`
  - `SendNotification` shows how to integrate external channels `Pipeline/components.py:249`

## Execution and parameters

- Typical command
  - `python Pipeline/voicebot_with_datapizza-ai.py --config Pipeline/voicebot_functional_pipeline.yaml`
- Quick overrides (CLI → YAML → defaults)
  - `--sec 30` recording duration
  - `--sr 16000` sample rate
  - `--audio session.wav` audio path
  - `--out Pipeline/voicebot_report.md` MD report
  - `--model gemini-2.5-flash` model

## Expected output

- Markdown report with sections
  - Transcription
  - Summary (normalized bullets)
  - Rewrite
  - Footer with sentiment, file and timestamp
- Example file: `Pipeline/voicebot_report.md`

## FAQ / Troubleshooting

- Missing GOOGLE_API_KEY
  - Add `.env` with `GOOGLE_API_KEY=...` and reopen the terminal.
- sounddevice not found / PortAudio
  - `pip install sounddevice soundfile` and on Linux install `portaudio19-dev`.
- No audio recorded
  - Check microphone permissions and correct input device.
- Mermaid not rendering
  - Use the ASCII diagram or enable a compatible viewer.

## Quick extensions (ideas)

- Add `SentimentChecker` for richer conditions (`Pipeline/components.py:272`).
- Branch on multiple sentiments (positive/neutral/angry) using different sub‑pipelines.
- Move variable parameters (duration, model, output) into your YAML and version them.
