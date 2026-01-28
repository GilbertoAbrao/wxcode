"""OpenAIProvider - Provider para OpenAI GPT."""

import os
from typing import Any

from ..models import ConversionContext, LLMResponse, LLMResponseError
from .base import BaseLLMProvider
from .prompts import SYSTEM_PROMPT

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None  # type: ignore


class OpenAIProvider(BaseLLMProvider):
    """Provider para OpenAI GPT."""

    # Preços por milhão de tokens
    PRICING: dict[str, dict[str, float]] = {
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    }

    DEFAULT_MODEL = "gpt-4o"

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        max_retries: int = 3,
        timeout: int = 120,
    ):
        """Inicializa o provider OpenAI.

        Args:
            model: Modelo a usar (default: gpt-4o)
            api_key: Chave da API OpenAI (usa OPENAI_API_KEY se não fornecida)
            max_retries: Número máximo de tentativas
            timeout: Timeout em segundos

        Raises:
            LLMResponseError: Se openai não estiver instalado ou API key não configurada
        """
        if not OPENAI_AVAILABLE:
            raise LLMResponseError(
                "OpenAI package not installed. Run: pip install openai"
            )

        super().__init__(model or self.DEFAULT_MODEL, max_retries, timeout)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise LLMResponseError("OPENAI_API_KEY not found")
        self.client = openai.OpenAI(api_key=self.api_key)

    @property
    def name(self) -> str:
        """Nome do provider."""
        return "openai"

    async def convert(self, context: ConversionContext) -> LLMResponse:
        """Envia contexto para o GPT e retorna resposta.

        Args:
            context: Contexto da conversão

        Returns:
            LLMResponse com conteúdo e métricas de uso

        Raises:
            LLMResponseError: Se a chamada falhar após retries
        """
        user_message = self._build_user_message(context)

        try:
            response = await self._call_with_retry(
                lambda: self._sync_call(user_message),
                (openai.RateLimitError, openai.APITimeoutError),
            )
        except openai.APIError as e:
            raise LLMResponseError(f"OpenAI API error: {e}") from e
        except Exception as e:
            raise LLMResponseError(f"Failed after retries: {e}") from e

        return LLMResponse(
            content=response["content"],
            input_tokens=response["input_tokens"],
            output_tokens=response["output_tokens"],
        )

    def _sync_call(self, user_message: str) -> dict[str, Any]:
        """Chamada síncrona para a API OpenAI.

        Args:
            user_message: Mensagem do usuário

        Returns:
            Dicionário com content, input_tokens, output_tokens
        """
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=8192,
            timeout=self.timeout,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )

        return {
            "content": response.choices[0].message.content or "",
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
        }

    def estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        """Estima custo em USD.

        Args:
            tokens_in: Número de tokens de entrada
            tokens_out: Número de tokens de saída

        Returns:
            Custo estimado em USD
        """
        pricing = self.PRICING.get(self.model, self.PRICING[self.DEFAULT_MODEL])
        return (tokens_in * pricing["input"] + tokens_out * pricing["output"]) / 1_000_000

    @classmethod
    def available_models(cls) -> list[str]:
        """Lista modelos disponíveis.

        Returns:
            Lista de modelos OpenAI suportados
        """
        return list(cls.PRICING.keys())
