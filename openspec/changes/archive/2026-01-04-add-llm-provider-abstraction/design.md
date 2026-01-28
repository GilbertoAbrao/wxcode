# Design: LLM Provider Abstraction

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    LLMProvider (Protocol)                   │
├─────────────────────────────────────────────────────────────┤
│  + name: str                                                │
│  + convert(context: ConversionContext) -> LLMResponse       │
│  + estimate_cost(tokens_in, tokens_out) -> float            │
│  + available_models() -> list[str]                          │
└─────────────────────────────────────────────────────────────┘
              △                    △                    △
              │                    │                    │
┌─────────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ AnthropicProvider   │  │  OpenAIProvider │  │  OllamaProvider │
├─────────────────────┤  ├─────────────────┤  ├─────────────────┤
│ claude-sonnet-4     │  │ gpt-4o          │  │ llama3.1        │
│ claude-opus-4       │  │ gpt-4o-mini     │  │ mistral         │
│ claude-haiku        │  │ gpt-4-turbo     │  │ codellama       │
└─────────────────────┘  └─────────────────┘  └─────────────────┘
```

## Components

### 1. LLMProvider Protocol

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class LLMProvider(Protocol):
    """Protocol para providers de LLM."""

    @property
    def name(self) -> str:
        """Nome do provider (anthropic, openai, ollama)."""
        ...

    @property
    def model(self) -> str:
        """Modelo em uso."""
        ...

    async def convert(self, context: ConversionContext) -> LLMResponse:
        """Executa conversão usando o LLM."""
        ...

    def estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        """Estima custo em USD (0.0 para providers gratuitos)."""
        ...

    @classmethod
    def available_models(cls) -> list[str]:
        """Lista modelos disponíveis para este provider."""
        ...
```

### 2. Base Provider Class

```python
class BaseLLMProvider:
    """Classe base com funcionalidades comuns."""

    def __init__(
        self,
        model: str,
        max_retries: int = 3,
        timeout: int = 120,
    ):
        self._model = model
        self.max_retries = max_retries
        self.timeout = timeout

    @property
    def model(self) -> str:
        return self._model

    def _build_user_message(self, context: ConversionContext) -> str:
        """Formata contexto como mensagem (compartilhado)."""
        # Código atual do LLMClient._build_user_message
        ...

    def _format_control(self, control: dict, indent: int = 0) -> str:
        """Formata controle (compartilhado)."""
        # Código atual do LLMClient._format_control
        ...
```

### 3. AnthropicProvider

```python
class AnthropicProvider(BaseLLMProvider):
    """Provider para Anthropic Claude."""

    name = "anthropic"

    # Preços por milhão de tokens
    PRICING = {
        "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
        "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
        "claude-3-5-haiku-20241022": {"input": 0.25, "output": 1.25},
    }

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        **kwargs,
    ):
        super().__init__(model or self.DEFAULT_MODEL, **kwargs)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise LLMResponseError("ANTHROPIC_API_KEY not found")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    async def convert(self, context: ConversionContext) -> LLMResponse:
        # Implementação atual do LLMClient
        ...

    def estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        pricing = self.PRICING.get(self.model, self.PRICING[self.DEFAULT_MODEL])
        return (tokens_in * pricing["input"] + tokens_out * pricing["output"]) / 1_000_000

    @classmethod
    def available_models(cls) -> list[str]:
        return list(cls.PRICING.keys())
```

### 4. OpenAIProvider

```python
class OpenAIProvider(BaseLLMProvider):
    """Provider para OpenAI GPT."""

    name = "openai"

    PRICING = {
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    }

    DEFAULT_MODEL = "gpt-4o"

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        **kwargs,
    ):
        super().__init__(model or self.DEFAULT_MODEL, **kwargs)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise LLMResponseError("OPENAI_API_KEY not found")
        self.client = openai.OpenAI(api_key=self.api_key)

    async def convert(self, context: ConversionContext) -> LLMResponse:
        user_message = self._build_user_message(context)
        response = await self._call_with_retry(user_message)
        return LLMResponse(
            content=response["content"],
            input_tokens=response["input_tokens"],
            output_tokens=response["output_tokens"],
        )

    def _sync_call(self, user_message: str) -> dict:
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
            "content": response.choices[0].message.content,
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        }

    def estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        pricing = self.PRICING.get(self.model, self.PRICING[self.DEFAULT_MODEL])
        return (tokens_in * pricing["input"] + tokens_out * pricing["output"]) / 1_000_000

    @classmethod
    def available_models(cls) -> list[str]:
        return list(cls.PRICING.keys())
```

### 5. OllamaProvider

```python
class OllamaProvider(BaseLLMProvider):
    """Provider para Ollama (modelos locais)."""

    name = "ollama"

    MODELS = ["llama3.1", "llama3.1:70b", "mistral", "codellama", "deepseek-coder"]
    DEFAULT_MODEL = "llama3.1"

    def __init__(
        self,
        model: str | None = None,
        base_url: str = "http://localhost:11434",
        **kwargs,
    ):
        super().__init__(model or self.DEFAULT_MODEL, **kwargs)
        self.base_url = base_url

    async def convert(self, context: ConversionContext) -> LLMResponse:
        user_message = self._build_user_message(context)

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
            content=data["response"],
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
        )

    def estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        return 0.0  # Ollama é gratuito (local)

    @classmethod
    def available_models(cls) -> list[str]:
        return cls.MODELS
```

### 6. Provider Factory

```python
PROVIDERS: dict[str, type[LLMProvider]] = {
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
    """Lista providers e seus modelos disponíveis."""
    return {
        name: cls.available_models()
        for name, cls in PROVIDERS.items()
    }
```

## File Structure

```
src/wxcode/llm_converter/
├── __init__.py              # Atualizar exports
├── models.py                # Sem mudanças
├── context_builder.py       # Sem mudanças
├── response_parser.py       # Sem mudanças
├── output_writer.py         # Sem mudanças
├── page_converter.py        # Usar LLMProvider ao invés de LLMClient
├── providers/               # NOVO
│   ├── __init__.py          # Exports + factory
│   ├── base.py              # BaseLLMProvider
│   ├── protocol.py          # LLMProvider Protocol
│   ├── anthropic.py         # AnthropicProvider
│   ├── openai.py            # OpenAIProvider
│   └── ollama.py            # OllamaProvider
└── llm_client.py            # DEPRECATED - manter para compatibilidade
```

## CLI Changes

```python
@app.command("convert-page")
def convert_page(
    page_name: str,
    output: Path = ...,
    provider: str = typer.Option(
        "anthropic",
        "--provider",
        "-P",
        help="LLM provider (anthropic, openai, ollama)",
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help="Modelo específico (usa default do provider se não fornecido)",
    ),
    ...
):
    ...
    from wxcode.llm_converter.providers import create_provider

    llm_provider = create_provider(provider, model=model)
    converter = PageConverter(db, output, llm_provider=llm_provider)
    ...
```

## Environment Variables

| Provider | Variable | Description |
|----------|----------|-------------|
| anthropic | `ANTHROPIC_API_KEY` | Chave API Anthropic |
| openai | `OPENAI_API_KEY` | Chave API OpenAI |
| ollama | `OLLAMA_BASE_URL` | URL do servidor Ollama (default: localhost:11434) |

## Model Recommendations

| Use Case | Provider | Model | Cost |
|----------|----------|-------|------|
| Produção (melhor qualidade) | anthropic | claude-sonnet-4 | $$$ |
| Produção (custo-benefício) | openai | gpt-4o-mini | $ |
| Desenvolvimento/Testes | ollama | llama3.1 | Grátis |
| Páginas complexas | anthropic | claude-opus-4 | $$$$ |

## Backward Compatibility

- `LLMClient` será mantido como alias para `AnthropicProvider`
- Código existente que usa `LLMClient` continuará funcionando
- Warning de deprecação será emitido

```python
# llm_client.py
import warnings
from .providers import AnthropicProvider

class LLMClient(AnthropicProvider):
    """DEPRECATED: Use AnthropicProvider ou create_provider() ao invés."""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "LLMClient is deprecated. Use create_provider('anthropic') instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
```
