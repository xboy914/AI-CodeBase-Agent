from types import SimpleNamespace

import pytest

from codebase_agent.config import Settings
from codebase_agent.providers import OpenAICompatibleProvider


class FakeEmbeddings:
    def create(self, **kwargs):
        assert kwargs["model"] == "nomic-embed-text"
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=[0.1, 0.2]) for _ in kwargs["input"]]
        )


class FakeCompletions:
    def create(self, **kwargs):
        assert kwargs["model"] == "qwen2.5-coder:7b"
        assert kwargs["messages"][0]["role"] == "system"
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Grounded answer"))]
        )


class FakeClient:
    embeddings = FakeEmbeddings()
    chat = SimpleNamespace(completions=FakeCompletions())


def ollama_settings() -> Settings:
    return Settings(
        ai_provider="ollama",
        embedding_model="nomic-embed-text",
        chat_model="qwen2.5-coder:7b",
    )


def test_ollama_defaults_to_local_openai_compatible_endpoint():
    provider = OpenAICompatibleProvider(ollama_settings(), client=FakeClient())

    assert provider._base_url() == "http://localhost:11434/v1"
    assert provider._api_key() == "ollama"


def test_provider_delegates_embeddings_and_chat_to_compatible_client():
    provider = OpenAICompatibleProvider(ollama_settings(), client=FakeClient())

    assert provider.embed(["one", "two"]) == [[0.1, 0.2], [0.1, 0.2]]
    assert provider.answer("system", "question") == "Grounded answer"


def test_custom_compatible_endpoint_and_key_are_supported():
    settings = Settings(
        ai_provider="openai",
        provider_base_url="http://vllm.internal/v1/",
        provider_api_key="local-key",
    )
    provider = OpenAICompatibleProvider(settings, client=FakeClient())

    assert provider._base_url() == "http://vllm.internal/v1"
    assert provider._api_key() == "local-key"


def test_openai_requires_credentials():
    provider = OpenAICompatibleProvider(Settings(), client=FakeClient())

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        provider._api_key()
