# llm-provider Specification

## Purpose

Abstração de providers de LLM para permitir uso de diferentes serviços (Anthropic, OpenAI, Ollama) no conversor de páginas. Permite flexibilidade de escolha, redução de custos e desenvolvimento local.

## ADDED Requirements

### Requirement: Define LLMProvider protocol

O sistema MUST definir um Protocol `LLMProvider` com interface comum para todos os providers.

#### Scenario: Protocol define métodos obrigatórios

**Given** o Protocol LLMProvider

**When** uma classe implementa o protocol

**Then** deve implementar:
- `name: str` - nome do provider
- `model: str` - modelo em uso
- `convert(context) -> LLMResponse` - executa conversão
- `estimate_cost(tokens_in, tokens_out) -> float` - estima custo
- `available_models() -> list[str]` - lista modelos

---

### Requirement: Implement AnthropicProvider

O sistema MUST implementar `AnthropicProvider` para Anthropic Claude.

#### Scenario: Criar provider com API key do ambiente

**Given** ANTHROPIC_API_KEY está configurada no ambiente

**When** AnthropicProvider() é instanciado sem api_key

**Then** deve usar a chave do ambiente

#### Scenario: Usar modelo default

**Given** provider instanciado sem modelo específico

**When** convert() é chamado

**Then** deve usar "claude-sonnet-4-20250514"

#### Scenario: Calcular custo corretamente

**Given** provider com modelo claude-sonnet-4

**When** estimate_cost(1000, 500) é chamado

**Then** deve retornar (1000 * 3.0 + 500 * 15.0) / 1_000_000 = 0.0105

#### Scenario: Listar modelos disponíveis

**When** AnthropicProvider.available_models() é chamado

**Then** deve retornar ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-3-5-haiku-20241022"]

---

### Requirement: Implement OpenAIProvider

O sistema MUST implementar `OpenAIProvider` para OpenAI GPT.

#### Scenario: Criar provider com API key do ambiente

**Given** OPENAI_API_KEY está configurada no ambiente

**When** OpenAIProvider() é instanciado sem api_key

**Then** deve usar a chave do ambiente

#### Scenario: Usar modelo default

**Given** provider instanciado sem modelo específico

**When** convert() é chamado

**Then** deve usar "gpt-4o"

#### Scenario: Formatar mensagens no padrão OpenAI

**Given** um ConversionContext

**When** convert() é chamado

**Then** deve enviar mensagens no formato:
```python
[
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_message}
]
```

#### Scenario: Extrair tokens de uso

**Given** resposta da API OpenAI

**When** response é processado

**Then** deve extrair:
- input_tokens de response.usage.prompt_tokens
- output_tokens de response.usage.completion_tokens

---

### Requirement: Implement OllamaProvider

O sistema MUST implementar `OllamaProvider` para modelos locais via Ollama.

#### Scenario: Usar URL default

**Given** provider instanciado sem base_url

**When** connect é feito

**Then** deve usar "http://localhost:11434"

#### Scenario: Usar modelo default

**Given** provider instanciado sem modelo específico

**When** convert() é chamado

**Then** deve usar "llama3.1"

#### Scenario: Custo zero para Ollama

**When** estimate_cost() é chamado com qualquer valor

**Then** deve retornar 0.0

#### Scenario: Chamar API Ollama corretamente

**Given** um ConversionContext

**When** convert() é chamado

**Then** deve fazer POST para /api/generate com:
```json
{
    "model": "llama3.1",
    "system": "SYSTEM_PROMPT",
    "prompt": "user_message",
    "stream": false
}
```

---

### Requirement: Implement provider factory

O sistema MUST implementar factory `create_provider()` para instanciar providers.

#### Scenario: Criar provider Anthropic

**When** create_provider("anthropic") é chamado

**Then** deve retornar instância de AnthropicProvider

#### Scenario: Criar provider OpenAI

**When** create_provider("openai") é chamado

**Then** deve retornar instância de OpenAIProvider

#### Scenario: Criar provider Ollama

**When** create_provider("ollama") é chamado

**Then** deve retornar instância de OllamaProvider

#### Scenario: Provider desconhecido

**When** create_provider("unknown") é chamado

**Then** deve lançar ValueError com mensagem listando providers disponíveis

#### Scenario: Passar modelo específico

**When** create_provider("openai", model="gpt-4o-mini") é chamado

**Then** deve criar OpenAIProvider com model="gpt-4o-mini"

---

### Requirement: CLI supports provider selection

O CLI MUST ter opção `--provider` para selecionar o provider.

#### Scenario: Usar provider default

**Given** comando sem --provider

**When** wxcode convert-page PAGE_Login é executado

**Then** deve usar provider "anthropic"

#### Scenario: Especificar provider OpenAI

**Given** comando com --provider openai

**When** wxcode convert-page PAGE_Login --provider openai é executado

**Then** deve usar OpenAIProvider

#### Scenario: Especificar provider e modelo

**Given** comando com --provider e --model

**When** wxcode convert-page PAGE_Login --provider openai --model gpt-4o-mini é executado

**Then** deve usar OpenAIProvider com modelo gpt-4o-mini

---

### Requirement: Maintain backward compatibility

O sistema MUST manter compatibilidade com código existente que usa LLMClient.

#### Scenario: LLMClient como alias

**Given** código que importa LLMClient

**When** LLMClient() é instanciado

**Then** deve funcionar como AnthropicProvider

#### Scenario: Emitir deprecation warning

**Given** código que usa LLMClient

**When** LLMClient() é instanciado

**Then** deve emitir DeprecationWarning

---

### Requirement: Share system prompt across providers

O sistema MUST usar o mesmo SYSTEM_PROMPT para todos os providers.

#### Scenario: System prompt compartilhado

**Given** qualquer provider

**When** convert() é chamado

**Then** deve usar SYSTEM_PROMPT definido em prompts.py

#### Scenario: System prompt contém regras de conversão

**Given** SYSTEM_PROMPT

**Then** deve conter:
- Regras de conversão WLanguage → Python
- Mapeamento de controles → HTML
- Formato de saída JSON esperado
