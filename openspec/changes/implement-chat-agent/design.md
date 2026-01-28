# Design: Chat AI Agent

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
├─────────────────────────────────────────────────────────────────┤
│  ChatInterface                                                  │
│  ├── useChat hook ─────────────────────┐                        │
│  │   └── WebSocket connection           │                       │
│  ├── ChatMessage (rendered messages)    │                       │
│  └── ChatInput (user input)            │                       │
└───────────────────────────────────────|──────────────────────────┘
                                        │ WebSocket
                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                        │
├─────────────────────────────────────────────────────────────────┤
│  WebSocket Endpoint (/ws/chat/{tenant}/{project})               │
│  │                                                              │
│  ▼                                                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      ChatAgent                            │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │  │
│  │  │  Guardrail  │  │  Classifier  │  │    Sanitizer    │   │  │
│  │  │  (input)    │  │  (message)   │  │    (output)     │   │  │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              ClaudeBridge / GSDInvoker                    │  │
│  │  (executa Claude Code CLI com --output-format json)       │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. MessageClassifier

Classifica mensagens JSON do Claude Code em tipos:

```python
class MessageType(Enum):
    QUESTION = "question"           # Pergunta simples esperando resposta
    MULTI_QUESTION = "multi_question"  # Múltiplas perguntas estruturadas
    INFO = "info"                   # Informação/status a ser exibida
    TOOL_RESULT = "tool_result"     # Resultado de execução de ferramenta
    ERROR = "error"                 # Mensagem de erro
    THINKING = "thinking"           # Processo de raciocínio (pode ocultar)
```

**Heurísticas de classificação:**
- `question`: Texto termina com `?` ou contém padrões como "What would you", "Which option"
- `multi_question`: JSON contém array de opções ou estrutura `AskUserQuestion`
- `tool_result`: Tipo é `tool_result` ou contém `tool_use`
- `error`: Tipo é `error` ou contém indicadores de falha
- `info`: Default para outros casos

### 2. Enhanced Guardrail

Extensão do Guardrail existente com:

**Novos padrões de prompt injection:**
```python
BLOCKED_INPUT_PATTERNS_EXTENDED = [
    # Jailbreak patterns
    (r"DAN\s+mode", "Jailbreak attempt"),
    (r"developer\s+mode", "Jailbreak attempt"),
    (r"pretend\s+you", "Roleplay attempt"),
    (r"act\s+as\s+if", "Roleplay attempt"),
    # Instruction override
    (r"new\s+instructions?:", "Override attempt"),
    (r"forget\s+(everything|all)", "Memory manipulation"),
    # Code execution
    (r"exec\s*\(", "Code execution"),
    (r"__import__", "Code execution"),
    (r"os\.system", "System command"),
]
```

**Novos padrões de sanitização de CLI:**
```python
OUTPUT_SANITIZE_PATTERNS_EXTENDED = [
    # CLI references
    (r"claude[\s-]?code", "[assistant]", re.IGNORECASE),
    (r"codex", "[assistant]", re.IGNORECASE),
    (r"gpt-?4", "[assistant]", re.IGNORECASE),
    (r"anthropic", "[provider]", re.IGNORECASE),
    (r"openai", "[provider]", re.IGNORECASE),
    # Internal commands
    (r"/gsd:\w+", "[workflow]"),
    (r"--output-format\s+\w+", ""),
    (r"--allowedTools\s+[\w,]+", ""),
    # Technical details
    (r"MCP\s+server", "[service]"),
    (r"tool_use_id:\s*[\w-]+", ""),
]
```

### 3. ChatAgent

Orquestrador principal:

```python
class ChatAgent:
    def __init__(self):
        self.classifier = MessageClassifier()
        self.guardrail = EnhancedGuardrail()
        self.sanitizer = OutputSanitizer()

    async def process_input(self, message: str) -> ProcessedInput:
        """Valida e processa input do usuário."""
        is_valid, error = self.guardrail.validate_input(message)
        if not is_valid:
            return ProcessedInput(valid=False, error=error)
        return ProcessedInput(valid=True, cleaned=message)

    async def process_output(self, json_data: dict) -> ProcessedMessage:
        """Processa saída JSON do Claude Code."""
        # Classifica o tipo de mensagem
        msg_type = self.classifier.classify(json_data)

        # Extrai conteúdo relevante
        content = self.extract_content(json_data)

        # Sanitiza referências sensíveis
        sanitized = self.sanitizer.sanitize(content)

        return ProcessedMessage(
            type=msg_type,
            content=sanitized,
            options=self.extract_options(json_data) if msg_type == MessageType.MULTI_QUESTION else None,
            metadata=self.extract_safe_metadata(json_data)
        )
```

### 4. Integration with WebSocket

Modificação do endpoint WebSocket existente:

```python
@router.websocket("/ws/chat/{tenant_id}/{project_id}")
async def websocket_chat(websocket: WebSocket, tenant_id: str, project_id: str):
    agent = ChatAgent()
    bridge = ClaudeBridgeFactory.get_or_create(tenant_id)

    await websocket.accept()

    while True:
        # Recebe mensagem do cliente
        data = await websocket.receive_json()
        message = data.get("message", "")

        # Processa input
        processed = await agent.process_input(message)
        if not processed.valid:
            await websocket.send_json({
                "type": "error",
                "message": processed.error
            })
            continue

        # Executa no Claude Code
        async for json_output in bridge.execute(processed.cleaned, project_id):
            # Processa output
            result = await agent.process_output(json_output)

            # Envia para cliente
            await websocket.send_json({
                "type": result.type.value,
                "content": result.content,
                "options": result.options,
                "metadata": result.metadata
            })
```

## Frontend Considerations

O frontend precisa tratar os tipos de mensagem:

| Message Type | UI Behavior |
|--------------|-------------|
| `question` | Exibir como pergunta, focar no input |
| `multi_question` | Renderizar opções como botões/radio |
| `info` | Exibir como texto normal |
| `tool_result` | Exibir em formato especial (colapsável?) |
| `error` | Exibir com estilo de erro |
| `thinking` | Ocultar ou mostrar indicador de loading |

## Security Considerations

1. **Defense in Depth**: Validação em múltiplas camadas (frontend, backend, agente)
2. **Fail Safe**: Em caso de dúvida na classificação, assume `info` (menos interativo)
3. **Logging**: Logar tentativas de injection para análise
4. **Rate Limiting**: Limitar frequência de mensagens por sessão
5. **Sanitização Agressiva**: Remover qualquer padrão suspeito, mesmo com falsos positivos

## Trade-offs

| Decision | Pros | Cons |
|----------|------|------|
| Classificação por regex | Rápido, previsível | Pode errar em edge cases |
| Sanitização agressiva | Mais seguro | Pode remover conteúdo legítimo |
| Fallback para `info` | Seguro | Pode perder interatividade |

## File Structure

```
src/wxcode/services/
├── chat_agent.py           # ChatAgent principal
├── message_classifier.py   # MessageClassifier
├── output_sanitizer.py     # OutputSanitizer
└── guardrail.py            # Guardrail existente (modificar)
```
