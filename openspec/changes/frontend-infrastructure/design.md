# Design: frontend-infrastructure

## Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│              API Routes + React Hooks                        │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  WebSocket/HTTP   │
                    └─────────┬─────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Guardrail  │──│ ClaudeBridge│──│   Token Tracker     │  │
│  │  (security) │  │  (executor) │  │   (metrics)         │  │
│  └─────────────┘  └──────┬──────┘  └─────────────────────┘  │
└──────────────────────────┼──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  Container A  │  │  Container B  │  │  Container N  │
│ (Claude Code) │  │ (Claude Code) │  │ (Claude Code) │
│   Tenant 1    │  │   Tenant 2    │  │   Tenant N    │
└───────────────┘  └───────────────┘  └───────────────┘
        ▲
        │
┌───────────────┐
│ OAuth Volume  │
│ (credentials) │
└───────────────┘
```

## Decisões Arquiteturais

### 1. Autenticação OAuth vs API Key

**Decisão:** OAuth via assinatura (Pro/Max/Team)

**Motivos:**
- Sem custos adicionais de API
- Usuário já paga assinatura
- Credenciais gerenciadas pelo Claude Code
- Refresh token automático

**Estrutura de Credenciais:**
```json
// ~/.claude/.credentials.json
{
  "claudeAiOauth": {
    "accessToken": "sk-ant-oat01-...",
    "refreshToken": "sk-ant-ort01-...",
    "expiresAt": 1748658860401,
    "scopes": ["user:inference", "user:profile"]
  }
}
```

### 2. Armazenamento de Métricas: MongoDB vs PostgreSQL

**Decisão:** MongoDB (Beanie)

**Motivos:**
- Consistência com o resto do projeto
- Já temos conexão configurada
- Schema flexível para métricas
- Async nativo com Motor/Beanie

### 3. WebSocket vs Server-Sent Events

**Decisão:** WebSocket

**Motivos:**
- Comunicação bidirecional necessária
- User pode enviar mensagens durante stream
- FastAPI tem suporte nativo
- Melhor controle de conexão

### 4. Guardrail: Backend vs Frontend

**Decisão:** Backend (única fonte de verdade)

**Motivos:**
- Frontend pode ser bypassado
- Validação centralizada
- Logs de segurança
- Menor duplicação

## Fluxo de Dados Detalhado

### Chat Message Flow

```
1. User envia mensagem
   │
   ▼
2. Frontend: useChat hook
   │ → Valida localmente (UX feedback)
   │ → Envia via WebSocket
   │
   ▼
3. Backend: WebSocket handler
   │ → Guardrail.validate_input()
   │   └─ Bloqueia: /commands, injection, etc
   │ → ClaudeBridge.execute()
   │   └─ Docker exec no container do tenant
   │
   ▼
4. Claude Code: stream-json output
   │ → {"type":"assistant","message":{...}}
   │ → {"usage":{"input_tokens":...}}
   │
   ▼
5. Backend: processar stream
   │ → TokenTracker.process_stream_line()
   │ → Guardrail.sanitize_output()
   │ → WebSocket.send(filtered_data)
   │
   ▼
6. Frontend: onMessage callback
   │ → Atualiza mensagens
   │ → Atualiza métricas de tokens
```

### Token Tracking Flow

```
1. Cada mensagem "assistant" do stream-json contém:
   {
     "type": "assistant",
     "message": {
       "usage": {
         "input_tokens": 1234,
         "cache_read_input_tokens": 567,
         "output_tokens": 89
       }
     }
   }

2. Ao final da execução:
   {
     "result": "...",
     "total_cost_usd": 0.2440755
   }

3. TokenTracker acumula durante a sessão
4. Ao encerrar, persiste em TokenUsageLog
```

## Modelos de Dados

### TokenUsageLog (MongoDB/Beanie)

```python
class TokenUsageLog(Document):
    tenant_id: str
    project_id: PydanticObjectId
    session_id: str
    change_id: Optional[str] = None

    # Métricas de tokens
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0

    # Custo e modelo
    total_cost_usd: float = 0.0
    model: str

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "token_usage_logs"
        indexes = [
            [("tenant_id", 1), ("project_id", 1)],
            [("created_at", -1)],
        ]
```

### ChatSession State

```python
@dataclass
class ChatSession:
    session_id: str
    tenant_id: str
    project_id: str
    messages: list[ChatMessage]
    token_tracker: TokenTracker
    created_at: datetime
```

## Estrutura de Arquivos

### Backend (Python)

```
src/wxcode/
├── models/
│   └── token_usage.py           # TokenUsageLog model
├── services/
│   ├── token_tracker.py         # Parser de métricas
│   ├── guardrail.py             # Validação e sanitização
│   ├── claude_bridge.py         # Execução em containers
│   └── subscription_limits.py   # API de limites (stub)
└── api/
    └── websocket.py             # WebSocket endpoint
```

### Frontend (TypeScript)

```
frontend/src/
├── app/
│   └── api/
│       └── [...path]/
│           └── route.ts         # Proxy para FastAPI
├── lib/
│   └── websocket.ts             # WebSocket client class
└── hooks/
    ├── useChat.ts               # Hook de chat com streaming
    └── useTokenUsage.ts         # Hook de métricas
```

## Scripts e Docker

### setup-auth.sh

Script interativo para autenticar Claude Code e salvar credenciais em volume Docker:

```bash
#!/bin/bash
# Cria volume e executa claude login
docker volume create claude-credentials
docker run -it --rm \
  -v claude-credentials:/home/node/.claude \
  node:22-slim \
  npx -y @anthropic-ai/claude-code login
```

### docker-compose.yml (adições)

```yaml
services:
  # ... existentes ...

  claude-worker:
    image: node:22-slim
    volumes:
      - claude-credentials:/home/node/.claude:ro
      - ./workspace:/workspace
    working_dir: /workspace
    networks:
      - wx-network
    # Container fica em standby, executado via docker exec

volumes:
  claude-credentials:
    external: true  # Criado por setup-auth.sh
```

## Segurança

### Padrões Bloqueados (Input)

| Padrão | Descrição |
|--------|-----------|
| `^/\w+` | Comandos slash |
| `ignore previous` | Prompt injection |
| `system prompt` | Tentativa de leak |
| `ANTHROPIC_API_KEY` | Credenciais |
| `rm -rf` | Comandos destrutivos |
| `sudo` | Elevação de privilégio |

### Padrões Sanitizados (Output)

| Padrão | Substituição |
|--------|--------------|
| `claude -p` | `[assistant]` |
| `~/.claude` | `[config]` |
| `sk-ant-*` | `[token]` |
| `/workspace/tenant/` | (removido) |

### Ferramentas Permitidas por Contexto

| Contexto | Ferramentas |
|----------|-------------|
| analysis | Read, Grep, Glob |
| conversion | Read, Write, Edit, Bash(npm:*) |
| review | Read, Grep |

## API Endpoints

### WebSocket

```
WS /ws/chat/{project_id}

Client → Server:
{
  "type": "message",
  "content": "Converta WIN_Principal para React",
  "context": "conversion"
}

Server → Client:
{
  "type": "assistant_chunk",
  "content": "Analisando...",
  "usage": {...}
}

{
  "type": "session_end",
  "total_cost_usd": 0.24,
  "usage_summary": {...}
}
```

### REST (via proxy)

```
GET  /api/projects/{id}/token-usage
POST /api/projects/{id}/chat (fallback se WS falhar)
```

## Próximos Passos (Fase 3)

Após esta infraestrutura estar pronta:
- Monaco Editor com syntax highlighting
- React Flow para grafo
- XTerm.js para terminal
- ChatInterface usando useChat hook
