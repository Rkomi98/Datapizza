"""Custom client example that wraps the Ollama HTTP API for DatapizzaAI.

First install Ollama (`curl -fsSL https://ollama.com/install.sh | sh`), pull a
model (`ollama pull gemma3n:e2b`), and start the daemon (`ollama serve`).
Running locally lets you iterate quickly while keeping the familiar `invoke`
contract from DatapizzaAI clients. This adapter targets the `/api/chat` endpoint.
"""

from __future__ import annotations

import requests
from typing import Optional

from datapizza.clients import ClientResponse
from datapizza.memory import Memory
from datapizza.type import TextBlock


class OllamaClient:
    """Simple Ollama adapter exposing the DatapizzaAI client interface."""

    def __init__(self, model: str = "gemma3n:e2b", base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def _build_messages(self, input_text: str | None, memory: Optional[Memory]) -> list[dict[str, str]]:
        """Convert DatapizzaAI memory into Ollama chat messages."""
        messages: list[dict[str, str]] = []
        if memory is not None:
            for turn in memory.memory:
                role = turn.role.value if hasattr(turn.role, "value") else str(turn.role)
                content = " ".join(getattr(block, "content", "") for block in turn.blocks)
                if content:
                    messages.append({"role": role, "content": content})
        if input_text:
            messages.append({"role": "user", "content": input_text})
        return messages

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Very rough token estimation based on word count."""
        return int(len(text.split()) * 1.3)

    def invoke(self, input_text: str | None = None, memory: Optional[Memory] = None) -> ClientResponse:
        """Invoke Ollama's chat endpoint and return a DatapizzaAI response."""
        messages = self._build_messages(input_text, memory)
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - defensive guard
            return ClientResponse(
                content=[TextBlock(content=f"Errore connessione Ollama: {exc}")],
                prompt_tokens_used=0,
                completion_tokens_used=0,
                stop_reason="error",
            )

        data = response.json()
        text = data.get("message", {}).get("content", "").strip()
        if not text:
            text = str(data)

        prompt_text = " ".join(message["content"] for message in messages)
        prompt_tokens = self._estimate_tokens(prompt_text)
        completion_tokens = self._estimate_tokens(text)

        return ClientResponse(
            content=[TextBlock(content=text)],
            prompt_tokens_used=prompt_tokens,
            completion_tokens_used=completion_tokens,
            stop_reason="stop",
        )


if __name__ == "__main__":
    client = OllamaClient()
    result = client.invoke("Riassumi in una frase il teorema di Pitagora.")

    print(f"Risposta: {result.text}")
    print(f"Token prompt: {result.prompt_tokens_used}")
    print(f"Token completion: {result.completion_tokens_used}")
