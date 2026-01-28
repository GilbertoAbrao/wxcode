"""AnthropicProvider - Provider para Anthropic Claude."""

import os
from typing import Any

import anthropic

from ..models import ConversionContext, LLMResponse, LLMResponseError, ProcedureContext
from .base import BaseLLMProvider
from .prompts import SYSTEM_PROMPT, PROCEDURE_SYSTEM_PROMPT


class AnthropicProvider(BaseLLMProvider):
    """Provider para Anthropic Claude."""

    # Preços por milhão de tokens
    PRICING: dict[str, dict[str, float]] = {
        "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
        "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
        "claude-3-5-haiku-20241022": {"input": 0.25, "output": 1.25},
    }

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        max_retries: int = 3,
        timeout: int = 120,
    ):
        """Inicializa o provider Anthropic.

        Args:
            model: Modelo a usar (default: claude-sonnet-4-20250514)
            api_key: Chave da API Anthropic (usa WXCODE_LLM_KEY ou ANTHROPIC_API_KEY)
            max_retries: Número máximo de tentativas
            timeout: Timeout em segundos

        Raises:
            LLMResponseError: Se nenhuma API key estiver configurada
        """
        super().__init__(model or self.DEFAULT_MODEL, max_retries, timeout)
        # Prefer custom variable name (avoids leaking to subprocesses like Claude CLI)
        # Falls back to standard name for backwards compatibility
        self.api_key = (
            api_key
            or os.environ.get("WXCODE_LLM_KEY")
            or os.environ.get("ANTHROPIC_API_KEY")
        )
        if not self.api_key:
            raise LLMResponseError(
                "API key not found. Set WXCODE_LLM_KEY or ANTHROPIC_API_KEY"
            )
        self.client = anthropic.Anthropic(api_key=self.api_key)

    @property
    def name(self) -> str:
        """Nome do provider."""
        return "anthropic"

    async def convert(self, context: ConversionContext) -> LLMResponse:
        """Envia contexto para o Claude e retorna resposta.

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
                (anthropic.RateLimitError, anthropic.APITimeoutError),
            )
        except anthropic.APIError as e:
            raise LLMResponseError(f"Anthropic API error: {e}") from e
        except Exception as e:
            raise LLMResponseError(f"Failed after retries: {e}") from e

        return LLMResponse(
            content=response["content"],
            input_tokens=response["input_tokens"],
            output_tokens=response["output_tokens"],
        )

    async def convert_procedure(self, context: ProcedureContext) -> LLMResponse:
        """Envia contexto de procedure group para o Claude e retorna resposta.

        Args:
            context: Contexto do procedure group

        Returns:
            LLMResponse com conteúdo e métricas de uso

        Raises:
            LLMResponseError: Se a chamada falhar após retries
        """
        user_message = self._build_procedure_user_message(context)

        try:
            response = await self._call_with_retry(
                lambda: self._sync_call_procedure(user_message),
                (anthropic.RateLimitError, anthropic.APITimeoutError),
            )
        except anthropic.APIError as e:
            raise LLMResponseError(f"Anthropic API error: {e}") from e
        except Exception as e:
            raise LLMResponseError(f"Failed after retries: {e}") from e

        return LLMResponse(
            content=response["content"],
            input_tokens=response["input_tokens"],
            output_tokens=response["output_tokens"],
        )

    def _sync_call_procedure(self, user_message: str) -> dict[str, Any]:
        """Chamada síncrona para conversão de procedures.

        Args:
            user_message: Mensagem do usuário

        Returns:
            Dicionário com content, input_tokens, output_tokens
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            timeout=self.timeout,
            system=PROCEDURE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        # Extrair conteúdo de texto
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return {
            "content": content,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

    def _sync_call(self, user_message: str) -> dict[str, Any]:
        """Chamada síncrona para a API Anthropic.

        Args:
            user_message: Mensagem do usuário

        Returns:
            Dicionário com content, input_tokens, output_tokens
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            timeout=self.timeout,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        # Extrair conteúdo de texto
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return {
            "content": content,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
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
            Lista de modelos Anthropic suportados
        """
        return list(cls.PRICING.keys())
