from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import sounddevice as sd
import soundfile as sf

from datapizzai.clients import ClientFactory
from datapizzai.core.models import PipelineComponent
from datapizzai.type import Media, MediaBlock, TextBlock


class RecordAudio(PipelineComponent):
    """Registra audio mono PCM16 e restituisce il percorso come {"audio_path": path}."""

    def _run(self, path: str = "session.wav", seconds: int = 20, sample_rate: int = 16000) -> Dict[str, str]:
        return self._record_audio(path, seconds, sample_rate)

    async def _a_run(self, path: str = "session.wav", seconds: int = 20, sample_rate: int = 16000) -> Dict[str, str]:
        return self._record_audio(path, seconds, sample_rate)

    def _record_audio(self, path: str, seconds: int, sample_rate: int) -> Dict[str, str]:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        print(f"🎙️ Recording {seconds}s @ {sample_rate}Hz → {path}")
        data = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
        sd.wait()
        sf.write(path, data, sample_rate)
        print(f"✅ Saved: {path}")
        return {"audio_path": path}


class GeminiAudioAnalyzer(PipelineComponent):
    """Invia un audio a Gemini 2.5 Flash e restituisce JSON con trascrizione, bullet, riscrittura, sentiment."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", temperature: float = 0.4):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    def _run(self, audio_path=None, **kwargs) -> Dict[str, Any]:
        # Gestisci sia stringa che dict in input
        if isinstance(audio_path, dict):
            path = audio_path.get("audio_path")
        elif isinstance(audio_path, str):
            path = audio_path
        else:
            # Prova a prendere da kwargs
            path = kwargs.get("audio_path") 
        
        if not path:
            raise ValueError("Parametro audio_path mancante")
        
        return self._analyze_audio(path)

    async def _a_run(self, audio_path=None, **kwargs) -> Dict[str, Any]:
        # Gestisci sia stringa che dict in input
        if isinstance(audio_path, dict):
            path = audio_path.get("audio_path")
        elif isinstance(audio_path, str):
            path = audio_path
        else:
            # Prova a prendere da kwargs
            path = kwargs.get("audio_path")
        
        if not path:
            raise ValueError("Parametro audio_path mancante")
            
        return self._analyze_audio(path)

    def _analyze_audio(self, audio_path: str) -> Dict[str, Any]:
        client = ClientFactory.create(
            provider="google",
            api_key=self.api_key,
            model=self.model,
            system_prompt=(
                "Sei un analista vocale. Restituisci JSON valido con chiavi: "
                "transcript (string), bullets (array di string), rewrite (string), "
                "sentiment (enum: angry|negative|neutral|positive|happy)."
            ),
            temperature=self.temperature,
        )

        media = Media(extension="wav", media_type="audio", source_type="path", source=audio_path)

        prompt = (
            "Analizza l'audio fornito. 1) Trascrivi con punteggiatura. "
            "2) Riassumi in <=8 bullet. 3) Riscrivi in 5-8 frasi. "
            "4) Stima sentiment (angry/negative/neutral/positive/happy). "
            "Rispondi SOLO con JSON compattato, senza testo extra."
        )

        resp = client.invoke([TextBlock(content=prompt), MediaBlock(media=media)])
        text = (resp.text or "").strip()

        # Prova a parsare JSON; fallback minimale se fallisce
        try:
            data = json.loads(text)
            assert isinstance(data, dict)
        except Exception:
            data = {
                "transcript": text,
                "bullets": [],
                "rewrite": text,
                "sentiment": "neutral",
            }

        # Aggiungi un semplice report Markdown pronto
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines: List[str] = []
        lines.append("## Trascrizione")
        lines.append(data.get("transcript") or "")
        lines.append("")
        lines.append("## Riassunto (bullet)")
        bullets = data.get("bullets") or []
        lines += [f"- {b}" for b in bullets]
        lines.append("")
        lines.append("## Riscrittura")
        lines.append(data.get("rewrite") or "")
        lines.append("")
        lines.append(f"_Sentiment_: {data.get('sentiment', 'neutral')} | _File_: `{audio_path}` | _Ts_: {ts}")

        data["report_markdown"] = "\n".join(lines) + "\n"
        return data


class ExtractKey(PipelineComponent):
    """Estrae una chiave da un dict (es. bullets da analyze)."""

    def __init__(self, key: str):
        self.key = key

    def _run(self, item=None, **kwargs):
        # Gestisci diversi modi di passaggio parametri
        data = item
        if data is None:
            # Prova a prendere dai kwargs
            if len(kwargs) == 1:
                data = list(kwargs.values())[0]
            else:
                data = kwargs
        
        if not isinstance(data, dict):
            return []
            
        return data.get(self.key, [])

    async def _a_run(self, item=None, **kwargs):
        # Gestisci diversi modi di passaggio parametri
        data = item
        if data is None:
            # Prova a prendere dai kwargs
            if len(kwargs) == 1:
                data = list(kwargs.values())[0]
            else:
                data = kwargs
        
        if not isinstance(data, dict):
            return []
            
        return data.get(self.key, [])


class BulletPointNormalizer(PipelineComponent):
    """Normalizza ogni bullet in stringa unica con prefisso '- ' e trimming."""

    def _run(self, item=None, **kwargs) -> str:
        # Gestisci diversi modi di passaggio parametri
        data = item
        if data is None and kwargs:
            data = list(kwargs.values())[0] if len(kwargs) == 1 else kwargs
        
        return self._normalize_bullet(data)

    async def _a_run(self, item=None, **kwargs) -> str:
        # Gestisci diversi modi di passaggio parametri
        data = item
        if data is None and kwargs:
            data = list(kwargs.values())[0] if len(kwargs) == 1 else kwargs
        
        return self._normalize_bullet(data)

    def _normalize_bullet(self, item: Any) -> str:
        s = str(item).strip()
        s = s.lstrip("-• ").strip()
        # Capitalizzazione soft
        if s and s[0].islower():
            s = s[0].upper() + s[1:]
        return f"- {s}"


class BuildReport(PipelineComponent):
    """Scrive su disco il report markdown costruito dall'analyzer, opzionalmente sostituendo i bullet normalizzati."""

    def _run(self, analysis=None, out_path: str = "Pipeline/voicebot_report.md", normalized_bullets: Optional[List[str]] = None, **kwargs) -> str:
        # Gestisci diversi modi di passaggio parametri
        if analysis is None:
            analysis = kwargs.get("analysis") or kwargs
        
        return self._build_report(analysis, out_path, normalized_bullets)

    async def _a_run(self, analysis=None, out_path: str = "Pipeline/voicebot_report.md", normalized_bullets: Optional[List[str]] = None, **kwargs) -> str:
        # Gestisci diversi modi di passaggio parametri
        if analysis is None:
            analysis = kwargs.get("analysis") or kwargs
            
        return self._build_report(analysis, out_path, normalized_bullets)

    def _build_report(self, analysis: Dict[str, Any], out_path: str, normalized_bullets: Optional[List[str]] = None) -> str:
        md = analysis.get("report_markdown") or ""
        
        # Se abbiamo bullet normalizzati, sostituiamoli nel markdown
        if normalized_bullets:
            # Ricostruisce la sezione bullet
            lines = md.split('\n')
            new_lines = []
            in_bullet_section = False
            
            for line in lines:
                if line.startswith("## Riassunto (bullet)"):
                    new_lines.append(line)
                    in_bullet_section = True
                elif in_bullet_section and line.startswith("##"):
                    # Aggiungi i bullet normalizzati e poi la nuova sezione
                    new_lines.extend(normalized_bullets)
                    new_lines.append("")
                    new_lines.append(line)
                    in_bullet_section = False
                elif in_bullet_section and line.startswith("- "):
                    # Salta i bullet originali
                    continue
                else:
                    new_lines.append(line)
                    
            if in_bullet_section:  # Se eravamo ancora nella sezione bullet alla fine
                new_lines.extend(normalized_bullets)
                
            md = '\n'.join(new_lines)
        
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"📝 Report salvato in: {out_path}")
        return out_path


class SendNotification(PipelineComponent):
    """Placeholder: invia una notifica se il sentiment è arrabbiato (simulato)."""

    def _run(self, sentiment: str = "angry", analysis: Optional[Dict[str, Any]] = None) -> str:
        return self._send_notification(sentiment, analysis)

    async def _a_run(self, sentiment: str = "angry", analysis: Optional[Dict[str, Any]] = None) -> str:
        return self._send_notification(sentiment, analysis)

    def _send_notification(self, sentiment: str, analysis: Optional[Dict[str, Any]]) -> str:
        # Qui potresti integrare email/Slack/etc.
        transcript = ""
        if analysis and "transcript" in analysis:
            transcript = analysis["transcript"][:100] + "..." if len(analysis["transcript"]) > 100 else analysis["transcript"]
            
        msg = f"⚠️ Utente con sentiment '{sentiment}' rilevato!\n"
        if transcript:
            msg += f"Trascrizione: {transcript}\n"
        msg += "Notifica inviata al team di supporto."
        print(msg)
        return msg


class SentimentChecker(PipelineComponent):
    """Controlla se il sentiment è arrabbiato."""

    def _run(self, analysis: Dict[str, Any]) -> bool:
        sentiment = analysis.get("sentiment", "neutral").lower()
        return sentiment in ["angry", "very_angry", "furious"]

    async def _a_run(self, analysis: Dict[str, Any]) -> bool:
        sentiment = analysis.get("sentiment", "neutral").lower()
        return sentiment in ["angry", "very_angry", "furious"]

