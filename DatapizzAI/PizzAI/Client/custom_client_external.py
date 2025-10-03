"""Custom client example integrating IBM WatsonX with DatapizzaAI.

This module shows how to wrap an external provider that is not bundled with
DatapizzaAI and expose the same `invoke` interface used by native clients.
Configure the following environment variables before running the example:
`IBM_WATSONX_API_KEY`, `IBM_WATSONX_URL`, and `IBM_WATSONX_PROJECT_ID`.
The adapter uses IBM WatsonX, but the pattern works for any REST provider.
"""

from __future__ import annotations

import os
from typing import Optional

from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

from datapizza.clients import ClientResponse
from datapizza.memory import Memory
from datapizza.type import TextBlock


class IBMWatsonXClient:
    """Adapter that makes IBM WatsonX behave like a DatapizzaAI client."""

    def __init__(self, model_id: str = "ibm/granite-3-2-8b-instruct", temperature: float = 0.7) -> None:
        self.model_id = model_id
        self.temperature = temperature

        # Configure IBM credentials once during initialization.
        self.credentials = Credentials(
            url=os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
            api_key=os.getenv("IBM_WATSONX_API_KEY"),
        )

        # Instantiate the low-level API client and select the project.
        self.client = APIClient(self.credentials)
        self.project_id = os.getenv("IBM_WATSONX_PROJECT_ID")
        if self.project_id:
            self.client.set.default_project(self.project_id)

        # Create the model inference handle once to reuse open connections.
        self.model = self._initialize_model()

    def _initialize_model(self) -> ModelInference:
        """Create a reusable ModelInference instance."""
        model_params = {
            "max_new_tokens": 1_000,
            "temperature": self.temperature,
            "stop_sequences": ["Human:", "Assistant:"],
        }

        return ModelInference(
            model_id=self.model_id,
            api_client=self.client,
            params=model_params,
        )

    def _build_prompt(self, input_text: str | None, memory: Optional[Memory]) -> str:
        """Compose a conversational prompt combining memory and user input."""
        prompt_parts: list[str] = []

        if memory is not None:
            for turn in memory.memory:
                role = turn.role.value if hasattr(turn.role, "value") else str(turn.role)
                content = " ".join(getattr(block, "content", "") for block in turn.blocks)
                if not content:
                    continue
                if role.lower() == "user":
                    prompt_parts.append(f"Human: {content}")
                elif role.lower() == "assistant":
                    prompt_parts.append(f"Assistant: {content}")

        if input_text:
            prompt_parts.append(f"Human: {input_text}")

        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)

    def invoke(self, input_text: str | None = None, memory: Optional[Memory] = None) -> ClientResponse:
        """Call IBM WatsonX and return a DatapizzaAI-compatible response object."""
        prompt = self._build_prompt(input_text, memory)

        try:
            response = self.model.generate_text(prompt=prompt)
        except Exception as exc:  # pragma: no cover - defensive guard
            return ClientResponse(
                content=[TextBlock(content=f"Errore IBM Watson: {exc}")],
                prompt_tokens_used=0,
                completion_tokens_used=0,
                stop_reason="error",
            )

        if isinstance(response, dict):
            text = response.get("generated_text", "").strip()
            if text.startswith("Assistant:"):
                text = text[10:].strip()
        else:
            text = str(response).strip()

        # Rough token estimation – WatsonX does not expose usage metrics yet.
        estimated_prompt_tokens = int(len(prompt.split()) * 1.3)
        estimated_completion_tokens = int(len(text.split()) * 1.3)

        return ClientResponse(
            content=[TextBlock(content=text)],
            prompt_tokens_used=estimated_prompt_tokens,
            completion_tokens_used=estimated_completion_tokens,
            stop_reason="stop",
        )


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    client = IBMWatsonXClient(
        model_id="ibm/granite-3-2-8b-instruct",
        temperature=0.7,
    )

    result = client.invoke("Ciao! Presentati brevemente.")
    print(f"Risposta: {result.text}")
    print(f"Token usati: {result.prompt_tokens_used + result.completion_tokens_used}")
