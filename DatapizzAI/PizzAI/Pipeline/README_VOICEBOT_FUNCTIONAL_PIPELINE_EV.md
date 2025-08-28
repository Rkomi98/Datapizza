# Voicebot with FunctionalPipeline

## 1. Overview

This system implements a voicebot for voice analysis using datapizzai's `FunctionalPipeline`. The pipeline records audio, analyzes it through Gemini 2.5 Flash, and generates automatic reports with intelligent sentiment management.

### Key features

- Real-time audio recording
- Automatic analysis with transcription, summary and sentiment
- Modular pipeline with conditional branches
- Automatic notifications for angry users
- Structured markdown reports
- YAML configuration support

## 2. Pipeline architecture

### Components used

The pipeline uses the following `PipelineComponent` elements:

- `RecordAudio`: mono PCM16 audio recording
- `GeminiAudioAnalyzer`: comprehensive analysis with Gemini 2.5 Flash
- `ExtractKey`: extraction of specific data from results
- `BulletPointNormalizer`: bullet points normalization
- `BuildReport`: markdown report generation
- `SendNotification`: notification sending for negative sentiment

### Pipeline flow

1. **Recording**: capture audio for specified duration
2. **Analysis**: transcription, summary and sentiment analysis
3. **Extraction**: bullet points isolation from results
4. **Normalization**: bullet points format standardization (foreach)
5. **Conditional branch**: sentiment-based handling
   - If angry: send notification
   - If normal: generate report
6. **Output**: structured final result

## 3. Installation and configuration

### System requirements

```bash
pip install sounddevice soundfile python-dotenv pyyaml
```

### Environment setup

Create `.env` file in project root:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

### YAML configuration

The `voicebot_functional_pipeline.yaml` file contains configuration parameters:

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

## 4. Usage

### Basic execution

```bash
python Pipeline/voicebot_functional_complete.py --mode basic
```

### Execution with custom configuration

```bash
python Pipeline/voicebot_functional_complete.py \
    --config Pipeline/voicebot_functional_pipeline.yaml \
    --mode yaml \
    --sec 30 \
    --out custom_report.md
```

### Available modes

- `basic`: standard programmatic pipeline
- `yaml`: loading from YAML configuration
- `advanced`: pipeline with complex patterns and multiple branches

### CLI parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--config` | YAML configuration file | `voicebot_functional_pipeline.yaml` |
| `--mode` | Pipeline mode | `basic` |
| `--sec` | Recording duration (seconds) | `20` |
| `--sr` | Sample rate | `16000` |
| `--audio` | Audio file path | `session.wav` |
| `--out` | Output report path | `Pipeline/voicebot_report.md` |
| `--model` | Gemini model | `gemini-2.5-flash` |

## 5. Code examples

### Basic programmatic pipeline

```python
from datapizzai.pipeline import Dependency, FunctionalPipeline
from Pipeline.components import *

# Component initialization
recorder = RecordAudio()
analyzer = GeminiAudioAnalyzer(api_key=GOOGLE_API_KEY)
normalizer = BulletPointNormalizer()

# Sub-pipeline for notifications
notification_pipeline = (
    FunctionalPipeline()
    .run(name="send_notification", node=SendNotification())
)

# Main pipeline with branch
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

# Execution
results = pipeline.execute()
```

### Using foreach for normalization

```python
# Foreach to process bullet points list
normalize_pipeline = (
    FunctionalPipeline()
    .foreach(
        name="normalize_bullets",
        dependencies=[Dependency(node_name="extract_bullets")],
        do=BulletPointNormalizer(),
    )
)
```

### Conditional branch for sentiment

```python
# Branch based on sentiment analysis
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

## 6. Output structure

### Generated markdown report

```markdown
## Trascrizione
[Text transcribed from audio]

## Riassunto (bullet)
- Main point 1
- Main point 2
- Main point 3

## Riscrittura
[Reworked version of content]

_Sentiment_: neutral | _File_: session.wav | _Ts_: 2024-01-15 14:30:00
```

### Pipeline results

The `pipeline.execute()` call returns a dictionary with:

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
    "normalize_bullets": ["- Point 1", "- Point 2"],
    "generate_report": "Pipeline/voicebot_report.md"
}
```

## 7. Customization and extension

### Creating custom components

```python
from datapizzai.core.models import PipelineComponent

class CustomAnalyzer(PipelineComponent):
    def _run(self, data):
        # Custom analysis logic
        return processed_data
    
    async def _a_run(self, data):
        # Asynchronous version
        return processed_data
```

### Adding new branch conditions

```python
# Custom conditions for branching
custom_condition = lambda ctx: (
    len(ctx.get("transcript", "")) > 500 and
    "urgent" in ctx.get("transcript", "").lower()
)

pipeline.branch(
    condition=custom_condition,
    if_true=urgent_pipeline,
    if_false=normal_pipeline
)
```

### Advanced foreach patterns

```python
# Foreach with multiple dependencies
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

## 8. Troubleshooting

### Common errors

**Error: GOOGLE_API_KEY missing**
- Check for `.env` file presence
- Verify key is valid and active

**Error: sounddevice module not found**
- Install dependencies: `pip install sounddevice soundfile`
- On Linux: `sudo apt-get install portaudio19-dev`

**Error: Pipeline execution failed**
- Verify all components are properly initialized
- Check logs for component-specific errors

### Pipeline debugging

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Print pipeline status
results = pipeline.execute()
print("Available keys:", list(results.keys()))
for key, value in results.items():
    print(f"{key}: {type(value)}")
```

## 9. Best practices

### Error handling

- Implement validation in custom components
- Use try/catch in `_run()` methods
- Verify dependencies before execution

### Performance

- Use asynchronous components when possible
- Configure appropriate timeouts for audio recording
- Optimize Gemini prompts to reduce latency

### Maintainability

- Separate business logic from pipeline components
- Use YAML configuration for variable parameters
- Document complex branch conditions and dependencies
