"""LLM Providers module - Abstração de providers de LLM."""

from .anthropic import AnthropicProvider
from .base import BaseLLMProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider
from .protocol import LLMProvider
from .prompts import SYSTEM_PROMPT

# Registro de providers disponíveis
PROVIDERS: dict[str, type[BaseLLMProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def create_provider(
    provider_name: str = "anthropic",
    model: str | None = None,
    **kwargs,
) -> LLMProvider:
    """Cria uma instância de provider.

    Args:
        provider_name: Nome do provider (anthropic, openai, ollama)
        model: Modelo específico (usa default do provider se não fornecido)
        **kwargs: Argumentos adicionais para o provider

    Returns:
        Instância do provider

    Raises:
        ValueError: Se provider não existir
    """
    if provider_name not in PROVIDERS:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(f"Unknown provider '{provider_name}'. Available: {available}")

    provider_class = PROVIDERS[provider_name]
    return provider_class(model=model, **kwargs)


def list_providers() -> dict[str, list[str]]:
    """Lista providers e seus modelos disponíveis.

    Returns:
        Dicionário com provider_name -> lista de modelos
    """
    return {name: cls.available_models() for name, cls in PROVIDERS.items()}


__all__ = [
    "LLMProvider",
    "BaseLLMProvider",
    "AnthropicProvider",
    "OpenAIProvider",
    "OllamaProvider",
    "SYSTEM_PROMPT",
    "PROVIDERS",
    "create_provider",
    "list_providers",
]
