from typing import Protocol

from openai import OpenAI

from .config import Settings


class AIProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    def answer(self, system_prompt: str, user_prompt: str) -> str: ...


class OpenAICompatibleProvider:
    def __init__(self, settings: Settings, client: OpenAI | None = None):
        self.settings = settings
        self.client = client or OpenAI(
            api_key=self._api_key(),
            base_url=self._base_url(),
        )

    def _api_key(self) -> str:
        if self.settings.ai_provider == "ollama":
            return self.settings.provider_api_key or "ollama"
        key = self.settings.provider_api_key or self.settings.openai_api_key
        if not key:
            raise ValueError(
                "OPENAI_API_KEY or PROVIDER_API_KEY is required when AI_PROVIDER=openai"
            )
        return key

    def _base_url(self) -> str | None:
        if self.settings.provider_base_url:
            return self.settings.provider_base_url.rstrip("/")
        if self.settings.ai_provider == "ollama":
            return "http://localhost:11434/v1"
        return None

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=self.settings.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def answer(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.settings.chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        return content or ""


def build_provider(settings: Settings) -> AIProvider:
    return OpenAICompatibleProvider(settings)
