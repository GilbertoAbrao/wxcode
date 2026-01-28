# Tasks: add-llm-provider-abstraction

## Overview

Tornar o LLMClient agnóstico de provider, permitindo uso de Anthropic, OpenAI e Ollama.

**Dependência**: add-llm-page-converter (já implementado)

## Status

- [x] Task 1: Create providers module structure
- [x] Task 2: Create LLMProvider protocol and base class
- [x] Task 3: Extract SYSTEM_PROMPT to prompts.py
- [x] Task 4: Implement AnthropicProvider
- [x] Task 5: Implement OpenAIProvider
- [x] Task 6: Implement OllamaProvider
- [x] Task 7: Create provider factory
- [x] Task 8: Update PageConverter to use LLMProvider
- [x] Task 9: Update CLI with --provider option
- [x] Task 10: Deprecate LLMClient

---

## Task 1: Create providers module structure

**Objetivo**: Criar estrutura de diretórios para providers.

**Arquivos a criar**:
```
src/wxcode/llm_converter/providers/
├── __init__.py
├── protocol.py
├── base.py
├── anthropic.py
├── openai.py
└── ollama.py
```

**Validação**: Diretório criado com arquivos vazios.

---

## Task 2: Create LLMProvider protocol and base class

**Objetivo**: Definir interface comum e classe base.

**Arquivo**: `providers/protocol.py`
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class LLMProvider(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def model(self) -> str: ...
    async def convert(self, context: ConversionContext) -> LLMResponse: ...
    def estimate_cost(self, tokens_in: int, tokens_out: int) -> float: ...
    @classmethod
    def available_models(cls) -> list[str]: ...
```

**Arquivo**: `providers/base.py`
```python
class BaseLLMProvider:
    def __init__(self, model: str, max_retries: int = 3, timeout: int = 120): ...
    def _build_user_message(self, context: ConversionContext) -> str: ...
    def _format_control(self, control: dict, indent: int = 0) -> str: ...
    async def _call_with_retry(self, call_fn) -> dict: ...
```

**Validação**: Importar protocol e base sem erros.

---

## Task 3: Extract SYSTEM_PROMPT to prompts.py

**Objetivo**: Mover SYSTEM_PROMPT para arquivo compartilhado.

**Arquivo**: `providers/prompts.py`

Mover o SYSTEM_PROMPT de `llm_client.py` para `prompts.py`.

**Validação**: Import do SYSTEM_PROMPT funciona.

---

## Task 4: Implement AnthropicProvider

**Objetivo**: Extrair código de LLMClient para AnthropicProvider.

**Arquivo**: `providers/anthropic.py`

**Implementar**:
- `__init__` com api_key e model
- `convert()` usando anthropic SDK
- `estimate_cost()` com tabela de preços
- `available_models()` com modelos suportados

**Preços** (por milhão de tokens):
- claude-sonnet-4: input=$3, output=$15
- claude-opus-4: input=$15, output=$75
- claude-3-5-haiku: input=$0.25, output=$1.25

**Validação**: AnthropicProvider passa nos mesmos testes que LLMClient.

---

## Task 5: Implement OpenAIProvider

**Objetivo**: Criar provider para OpenAI.

**Dependência**: `pip install openai`

**Arquivo**: `providers/openai.py`

**Implementar**:
- `__init__` com api_key e model
- `convert()` usando openai SDK
- `estimate_cost()` com tabela de preços
- `available_models()` com modelos suportados

**Preços** (por milhão de tokens):
- gpt-4o: input=$2.5, output=$10
- gpt-4o-mini: input=$0.15, output=$0.60
- gpt-4-turbo: input=$10, output=$30

**Diferenças da API OpenAI**:
- Usa `chat.completions.create()`
- Mensagens em formato `[{"role": "system"}, {"role": "user"}]`
- Tokens em `response.usage.prompt_tokens` e `completion_tokens`

**Validação**: Testar com OPENAI_API_KEY configurada.

---

## Task 6: Implement OllamaProvider

**Objetivo**: Criar provider para Ollama (modelos locais).

**Dependência**: `pip install httpx` (já instalado)

**Arquivo**: `providers/ollama.py`

**Implementar**:
- `__init__` com base_url e model
- `convert()` usando httpx para chamar API REST
- `estimate_cost()` retornando 0.0
- `available_models()` com modelos comuns

**API Ollama**:
- POST /api/generate
- Body: `{"model": "...", "system": "...", "prompt": "...", "stream": false}`
- Response: `{"response": "...", "prompt_eval_count": N, "eval_count": N}`

**Validação**: Testar com Ollama rodando localmente.

---

## Task 7: Create provider factory

**Objetivo**: Criar factory para instanciar providers.

**Arquivo**: `providers/__init__.py`

**Implementar**:
```python
PROVIDERS = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}

def create_provider(provider_name: str, model: str | None = None, **kwargs) -> LLMProvider:
    ...

def list_providers() -> dict[str, list[str]]:
    ...
```

**Validação**: create_provider("anthropic") retorna AnthropicProvider.

---

## Task 8: Update PageConverter to use LLMProvider

**Objetivo**: Atualizar PageConverter para aceitar qualquer LLMProvider.

**Arquivo**: `page_converter.py`

**Mudanças**:
- Trocar type hint de `LLMClient` para `LLMProvider`
- Usar `provider.estimate_cost()` ao invés de cálculo hardcoded
- Atualizar docstrings

**Validação**: PageConverter funciona com AnthropicProvider.

---

## Task 9: Update CLI with --provider option

**Objetivo**: Adicionar opção --provider ao CLI.

**Arquivo**: `cli.py`

**Mudanças**:
```python
provider: str = typer.Option(
    "anthropic",
    "--provider",
    "-P",
    help="LLM provider (anthropic, openai, ollama)",
),
```

**Usar factory**:
```python
from wxcode.llm_converter.providers import create_provider
llm_provider = create_provider(provider, model=model)
```

**Validação**: `wxcode convert-page --help` mostra opção --provider.

---

## Task 10: Deprecate LLMClient

**Objetivo**: Manter LLMClient como alias deprecated.

**Arquivo**: `llm_client.py`

**Mudanças**:
```python
import warnings
from .providers import AnthropicProvider

class LLMClient(AnthropicProvider):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "LLMClient is deprecated. Use create_provider('anthropic') instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
```

**Validação**: Usar LLMClient emite warning.

---

## Dependencies

```
Task 1 (structure) ─┐
                    ├─▶ Task 4 (anthropic) ─┐
Task 2 (protocol)  ─┤                       │
Task 3 (prompts)   ─┼─▶ Task 5 (openai)    ─┼─▶ Task 7 (factory) ─▶ Task 8 (converter)
                    │                       │                              │
                    └─▶ Task 6 (ollama)    ─┘                              ▼
                                                                    Task 9 (CLI)
                                                                           │
                                                                           ▼
                                                                    Task 10 (deprecate)
```

## Parallelizable

Tasks 4, 5, 6 podem ser implementadas em paralelo após Tasks 1, 2, 3.
