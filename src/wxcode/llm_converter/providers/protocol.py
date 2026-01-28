"""LLMProvider Protocol - Interface comum para todos os providers."""

from typing import Protocol, runtime_checkable

from ..models import ConversionContext, LLMResponse


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol para providers de LLM.

    Define a interface que todos os providers devem implementar.
    """

    @property
    def name(self) -> str:
        """Nome do provider (anthropic, openai, ollama)."""
        ...

    @property
    def model(self) -> str:
        """Modelo em uso."""
        ...

    async def convert(self, context: ConversionContext) -> LLMResponse:
        """Executa conversão usando o LLM.

        Args:
            context: Contexto da conversão com controles, procedures, etc.

        Returns:
            LLMResponse com conteúdo e métricas de uso
        """
        ...

    def estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        """Estima custo em USD (0.0 para providers gratuitos).

        Args:
            tokens_in: Número de tokens de entrada
            tokens_out: Número de tokens de saída

        Returns:
            Custo estimado em USD
        """
        ...

    @classmethod
    def available_models(cls) -> list[str]:
        """Lista modelos disponíveis para este provider.

        Returns:
            Lista de nomes de modelos suportados
        """
        ...
