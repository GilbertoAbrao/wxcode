"""OllamaProvider - Provider para Ollama (modelos locais)."""

import os

import httpx

from ..models import ConversionContext, LLMResponse, LLMResponseError
from .base import BaseLLMProvider
from .prompts import SYSTEM_PROMPT


class OllamaProvider(BaseLLMProvider):
    """Provider para Ollama (modelos locais)."""

    # Modelos comuns disponíveis no Ollama
    MODELS: list[str] = [
        "llama3.1",
        "llama3.1:70b",
        "mistral",
        "codellama",
        "deepseek-coder",
    ]

    DEFAULT_MODEL = "llama3.1"
    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        max_retries: int = 3,
        timeout: int = 120,
    ):
        """Inicializa o provider Ollama.

        Args:
            model: Modelo a usar (default: llama3.1)
            base_url: URL do servidor Ollama (default: http://localhost:11434)
            max_retries: Número máximo de tentativas
            timeout: Timeout em segundos
        """
        super().__init__(model or self.DEFAULT_MODEL, max_retries, timeout)
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", self.DEFAULT_BASE_URL)

    @property
    def name(self) -> str:
        """Nome do provider."""
        return "ollama"

    async def convert(self, context: ConversionContext) -> LLMResponse:
        """Envia contexto para o Ollama e retorna resposta.

        Args:
            context: Contexto da conversão

        Returns:
            LLMResponse com conteúdo e métricas de uso

        Raises:
            LLMResponseError: Se a chamada falhar
        """
        user_message = self._build_user_message(context)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "system": SYSTEM_PROMPT,
                        "prompt": user_message,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()

            return LLMResponse(
                content=data.get("response", ""),
                input_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
            )

        except httpx.ConnectError as e:
            raise LLMResponseError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is Ollama running? (ollama serve)"
            ) from e
        except httpx.HTTPStatusError as e:
            raise LLMResponseError(f"Ollama HTTP error: {e}") from e
        except Exception as e:
            raise LLMResponseError(f"Ollama error: {e}") from e

    def estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        """Estima custo em USD.

        Args:
            tokens_in: Número de tokens de entrada (ignorado)
            tokens_out: Número de tokens de saída (ignorado)

        Returns:
            Sempre 0.0 - Ollama é gratuito (local)
        """
        return 0.0

    @classmethod
    def available_models(cls) -> list[str]:
        """Lista modelos disponíveis.

        Returns:
            Lista de modelos Ollama comuns
        """
        return cls.MODELS
