# Esercizio Semplificato: Audio → Trascrizione → Segmentazione → Riassunto

## Prerequisiti

- **Google API Key** con abilitato:
  - [Speech-to-Text](https://cloud.google.com/speech-to-text)
  - [Gemini](https://ai.google.dev/) (per riassunto/riscrittura)
- Python libs:
  ```bash
  pip install sounddevice soundfile pydub requests python-dotenv
  ```

## Pipeline semplice

## Diagramma della pipeline (Mermaid)

```mermaid
flowchart LR
    A[🎙️ Record audio] --> B[✂️ Segmentazione su silenzio]
    B --> C[🗣️ ASR Google Speech-to-Text<br/>(per segmento)]
    C --> D[🧠 Gemini<br/>Riassunto & Riscrittura]
    D --> E[📝 Report Markdown]
```



1. **Registra audio dal microfono**  
   Salva in `session.wav` (mono, 16kHz).
2. **Segmenta su silenzio**  
   Usa `pydub.silence.split_on_silence`.
3. **Trascrivi ogni segmento** con Google Speech-to-Text.  
4. **Invia i testi a Gemini**:  
   - Riassume in bullet point  
   - Riscrive in forma più leggibile  
5. **Stampa report finale** in Markdown.

## Codice minimale (tutto in uno)

```python
import os, requests, base64
import sounddevice as sd, soundfile as sf
from pydub import AudioSegment, silence
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# 1. Registra audio
def record_audio(file="session.wav", sec=20):
    print(f"🎙️ Registrazione {sec}s...")
    data = sd.rec(int(sec*16000), samplerate=16000, channels=1, dtype='int16')
    sd.wait()
    sf.write(file, data, 16000)
    print(f"Salvato {file}")

# 2. Segmenta su silenzio
def segment_audio(file):
    audio = AudioSegment.from_wav(file)
    return silence.split_on_silence(audio, min_silence_len=800, silence_thresh=-40)

# 3. Trascrizione con Google STT
def transcribe_wav(wav_bytes):
    url = f"https://speech.googleapis.com/v1/speech:recognize?key={API_KEY}"
    payload = {
      "config": {"encoding": "LINEAR16","sampleRateHertz":16000,"languageCode":"it-IT","enableAutomaticPunctuation":True},
      "audio": {"content": base64.b64encode(wav_bytes).decode("utf-8")}
    }
    r = requests.post(url, json=payload)
    return r.json().get("results",[{}])[0].get("alternatives",[{}])[0].get("transcript","")

# 4. Riassunto con Gemini
def summarize(texts):
    prompt = "Riassumi e riscrivi in bullet point:\n" + "\n".join(texts)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    r = requests.post(url, json={"contents":[{"parts":[{"text":prompt}]}]})
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

# ---- MAIN ----
record_audio()
segments = segment_audio("session.wav")

texts = []
for i, seg in enumerate(segments):
    fname = f"seg{i}.wav"
    seg.export(fname, format="wav")
    with open(fname,"rb") as f: texts.append(transcribe_wav(f.read()))

print("\n--- TESTO ORIGINALE ---")
print("\n".join(texts))

summary = summarize(texts)
print("\n--- RIASSUNTO ---")
print(summary)
```

## Come provarlo

1. Salva come `voicebot.py`  
2. Metti in `.env`:
   ```
   GOOGLE_API_KEY=la_tua_api_key
   ```
3. Avvia:
   ```bash
   python voicebot.py
   ```
4. Parla per 20s → segmenti → trascrizione → riassunto.
