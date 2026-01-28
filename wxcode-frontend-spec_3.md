# WXCODE Frontend - Especificação de Interface

## Visão Geral do Projeto

O **WXCODE Frontend** é uma interface web **inspirada no Lovable e Replit** que permite aos usuários converter projetos legados WinDev/WebDev para stacks modernos. A aplicação oferece:

- **Editor de código** com syntax highlighting
- **Visualização de grafos** de dependências interativa
- **Terminal integrado** para acompanhar execuções
- **Preview em tempo real** das conversões
- **Dashboard rico** com métricas e progresso

A aplicação opera em uma arquitetura **multi-tenant**, onde cada tenant roda em um **container Docker isolado** com Claude Code pré-instalado e autenticado.

---

## Estrutura do Projeto (Monorepo)

O frontend será desenvolvido **dentro do projeto wxcode** para manter contexto unificado:

```
wxcode/
├── src/wxcode/           # Backend Python (existente)
│   ├── api/
│   ├── core/
│   └── ...
├── frontend/                # Frontend Next.js (novo)
│   ├── src/
│   │   ├── app/            # App Router (páginas)
│   │   ├── components/     # Componentes React
│   │   ├── hooks/          # Custom hooks
│   │   ├── lib/            # Utilitários
│   │   └── types/          # TypeScript types
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── Dockerfile
├── openspec/               # Specs (existente)
├── docker-compose.yml      # Orquestração completa
└── CLAUDE.md
```

**Vantagens do Monorepo:**
- Claude Code tem contexto completo (backend + frontend)
- Tipos TypeScript podem ser gerados a partir dos Pydantic models
- Desenvolvimento mais ágil com mudanças coordenadas
- Deploy pode ser separado (containers independentes)

---

## Arquitetura Multi-Tenant

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Principal                        │
│                 (Next.js + FastAPI Gateway)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │    Guardrail      │
                    │   (Sanitização)   │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Container A  │     │  Container B  │     │  Container C  │
│   Tenant 1    │     │   Tenant 2    │     │   Tenant N    │
│ (Claude Code) │     │ (Claude Code) │     │ (Claude Code) │
└───────────────┘     └───────────────┘     └───────────────┘
```

---

## Autenticação Claude Code via Assinatura OAuth

Os containers utilizam **autenticação via assinatura** (Pro/Max/Team/Enterprise) em vez de API Key, evitando custos adicionais de API.

### Estrutura de Credenciais

As credenciais OAuth são armazenadas em `~/.claude/.credentials.json`:

```json
{
  "claudeAiOauth": {
    "accessToken": "sk-ant-oat01-...",
    "refreshToken": "sk-ant-ort01-...",
    "expiresAt": 1748658860401,
    "scopes": ["user:inference", "user:profile"]
  }
}
```

### Opções de Autenticação nos Containers

| Método | Descrição | Uso |
|--------|-----------|-----|
| **Setup Token** | Gerar token via `claude setup-token` no host | `CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...` |
| **Volume Mount** | Montar credenciais do host | `-v ~/.claude:/home/claude/.claude` |
| **Volume Compartilhado** | Volume Docker persistente | `-v claude-credentials:/home/claude/.claude` |

### Script de Setup Inicial

```bash
#!/bin/bash
# setup-auth.sh - Autentica Claude Code e salva credenciais em volume Docker

echo "=== Setup Claude Code Authentication ==="

docker run -it --rm \
  -v claude-credentials:/home/claude/.claude \
  --name claude-setup \
  node:22-slim \
  bash -c "
    npm install -g @anthropic-ai/claude-code && \
    useradd -m claude && \
    su claude -c 'claude login'
  "

echo "=== Credenciais salvas no volume 'claude-credentials' ==="
```

### Docker Compose para Container com Autenticação

```yaml
services:
  claude-code:
    image: node:22-slim
    volumes:
      - claude-credentials:/home/claude/.claude  # Credenciais OAuth
      - ./workspace:/workspace                    # Área de trabalho
    working_dir: /workspace
    command: >
      bash -c "
        npm install -g @anthropic-ai/claude-code &&
        useradd -m claude &&
        tail -f /dev/null
      "
    networks:
      - internal

volumes:
  claude-credentials:
    external: true  # Criado pelo setup-auth.sh
```

> ⚠️ **IMPORTANTE**: Se existir `ANTHROPIC_API_KEY` no ambiente, o Claude Code usará a API Key em vez da assinatura, resultando em cobranças. Certifique-se de NÃO definir essa variável nos containers.

---

## Sistema de Tracking de Consumo de Tokens

O sistema deve **capturar e registrar métricas de consumo** a partir do output do Claude Code em modo headless.

### Métricas Disponíveis no Output `stream-json`

Cada mensagem do tipo `assistant` inclui dados de uso:

```json
{
  "type": "assistant",
  "message": {
    "id": "msg_01Aj2DzG8ZmzJbLwH848x2Sc",
    "model": "claude-sonnet-4-20250514",
    "usage": {
      "input_tokens": 4,
      "cache_creation_input_tokens": 12582,
      "cache_read_input_tokens": 4802,
      "output_tokens": 12
    },
    "stop_reason": "end_turn"
  },
  "session_id": "e2393023-f234-46fc-a341-693936cbcdb8"
}
```

Ao final da execução, o output JSON também inclui custo total:

```json
{
  "result": "...",
  "session_id": "...",
  "total_cost_usd": 0.2440755,
  "usage": {
    "input_tokens": 4,
    "cache_creation_input_tokens": 12582,
    "cache_read_input_tokens": 4802,
    "output_tokens": 12
  }
}
```

### Modelo de Dados para Tracking

```python
# models/token_usage.py
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class TokenUsageLog(Base):
    __tablename__ = "token_usage_logs"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    session_id = Column(String, nullable=False)
    change_id = Column(String, ForeignKey("changes.id"), nullable=True)
    
    # Métricas de tokens
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cache_creation_tokens = Column(Integer, default=0)
    cache_read_tokens = Column(Integer, default=0)
    
    # Custo e modelo
    total_cost_usd = Column(Float, default=0.0)
    model = Column(String, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    tenant = relationship("Tenant", back_populates="usage_logs")
    project = relationship("Project", back_populates="usage_logs")
```

### Parser de Métricas do Output

```python
# services/token_tracker.py
import json
from typing import Optional, Dict, Any

class TokenTracker:
    """Extrai e registra métricas de tokens do output do Claude Code"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.current_session_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "total_cost_usd": 0.0,
            "model": None
        }
    
    def process_stream_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Processa uma linha do stream-json e extrai métricas"""
        try:
            data = json.loads(line)
            
            # Extrai usage de mensagens assistant
            if data.get("type") == "assistant":
                message = data.get("message", {})
                usage = message.get("usage", {})
                
                if usage:
                    self.current_session_usage["input_tokens"] += usage.get("input_tokens", 0)
                    self.current_session_usage["output_tokens"] += usage.get("output_tokens", 0)
                    self.current_session_usage["cache_creation_input_tokens"] += usage.get("cache_creation_input_tokens", 0)
                    self.current_session_usage["cache_read_input_tokens"] += usage.get("cache_read_input_tokens", 0)
                    self.current_session_usage["model"] = message.get("model")
            
            # Extrai custo total no resultado final
            if "total_cost_usd" in data:
                self.current_session_usage["total_cost_usd"] = data["total_cost_usd"]
            
            return data
            
        except json.JSONDecodeError:
            return None
    
    def save_usage(self, tenant_id: str, project_id: str, session_id: str, change_id: str = None):
        """Persiste as métricas no banco de dados"""
        log = TokenUsageLog(
            tenant_id=tenant_id,
            project_id=project_id,
            session_id=session_id,
            change_id=change_id,
            input_tokens=self.current_session_usage["input_tokens"],
            output_tokens=self.current_session_usage["output_tokens"],
            cache_creation_tokens=self.current_session_usage["cache_creation_input_tokens"],
            cache_read_tokens=self.current_session_usage["cache_read_input_tokens"],
            total_cost_usd=self.current_session_usage["total_cost_usd"],
            model=self.current_session_usage["model"]
        )
        self.db.add(log)
        self.db.commit()
        
        # Reset para próxima sessão
        self.reset()
        return log
    
    def reset(self):
        """Reseta contadores para nova sessão"""
        self.current_session_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "total_cost_usd": 0.0,
            "model": None
        }
```

### API de Limites de Uso da Assinatura

Além do tracking por comando, é possível consultar os **limites globais da assinatura** via API OAuth:

```python
# services/subscription_limits.py
import httpx
from typing import Optional, Dict

async def get_subscription_usage(access_token: str) -> Optional[Dict]:
    """Consulta limites de uso da assinatura Claude Pro/Max"""
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.anthropic.com/api/oauth/usage",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "wxcode/1.0",
                "Authorization": f"Bearer {access_token}",
                "anthropic-beta": "oauth-2025-04-20"
            }
        )
        
        if response.status_code == 200:
            return response.json()
        return None

# Exemplo de resposta:
# {
#   "five_hour": {
#     "utilization": 6.0,        # % utilizado nas últimas 5h
#     "resets_at": "2025-11-04T04:59:59.943648+00:00"
#   },
#   "seven_day": {
#     "utilization": 35.0,       # % utilizado nos últimos 7 dias
#     "resets_at": "2025-11-06T03:59:59.943679+00:00"
#   },
#   "seven_day_opus": {
#     "utilization": 0.0,        # % Opus utilizado (para Max)
#     "resets_at": null
#   }
# }
```

### Dashboard de Consumo (UI)

O frontend deve exibir métricas de consumo em tempo real:

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Consumo de Tokens - Projeto: MeuProjeto                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Sessão Atual                    Assinatura (5h / 7d)       │
│  ┌─────────────────────┐         ┌─────────────────────┐    │
│  │ Input:    12,586    │         │ 5h:  ████░░░░ 42%   │    │
│  │ Output:      847    │         │ 7d:  ██░░░░░░ 28%   │    │
│  │ Cache:    4,802     │         │ Reset: 2h 34m       │    │
│  │ Custo:    $0.24     │         └─────────────────────┘    │
│  └─────────────────────┘                                    │
│                                                             │
│  Histórico do Projeto           Top Elementos por Custo     │
│  ┌─────────────────────┐        ┌─────────────────────┐     │
│  │ 📈 [Gráfico 7 dias] │        │ 1. WIN_Principal $2.4│    │
│  │                     │        │ 2. CLS_Pedido   $1.8 │    │
│  │ Total: $12.47       │        │ 3. QRY_Vendas   $0.9 │    │
│  └─────────────────────┘        └─────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Estrutura de Componentes (Next.js)

### App Router Pages

```
frontend/src/app/
├── layout.tsx                    # Root layout (providers, theme)
├── page.tsx                      # Landing/redirect
├── dashboard/
│   └── page.tsx                  # Lista de projetos
├── project/
│   └── [id]/
│       ├── layout.tsx            # Layout do workspace
│       ├── page.tsx              # Workspace principal
│       ├── graph/
│       │   └── page.tsx          # Visualização do grafo
│       └── changes/
│           ├── page.tsx          # Lista de changes
│           └── [changeId]/
│               └── page.tsx      # Diff/review de change
└── api/                          # API Routes (proxy para FastAPI)
    └── [...path]/
        └── route.ts
```

### Componentes Principais

```
frontend/src/components/
├── ui/                           # shadcn/ui components
│   ├── button.tsx
│   ├── dialog.tsx
│   └── ...
├── layout/
│   ├── Sidebar.tsx               # Navegação lateral
│   ├── ResizablePanels.tsx       # Painéis redimensionáveis
│   └── Header.tsx
├── editor/
│   ├── MonacoEditor.tsx          # Editor de código
│   ├── DiffViewer.tsx            # Diff side-by-side
│   └── WLanguageHighlight.ts     # Syntax highlighting customizado
├── graph/
│   ├── DependencyGraph.tsx       # React Flow wrapper
│   ├── CustomNode.tsx            # Nó customizado
│   └── GraphControls.tsx
├── terminal/
│   ├── Terminal.tsx              # XTerm.js wrapper
│   └── TerminalOutput.tsx
├── chat/
│   ├── ChatInterface.tsx         # Interface de chat
│   ├── ChatMessage.tsx           # Mensagem individual
│   └── ChatInput.tsx             # Input com envio
├── project/
│   ├── ElementTree.tsx           # Árvore de elementos
│   ├── ChangeCard.tsx            # Card de change
│   └── TokenUsage.tsx            # Métricas de consumo
└── dashboard/
    ├── ProjectCard.tsx           # Card de projeto
    └── UsageChart.tsx            # Gráfico de consumo
```

### Custom Hooks

```typescript
// frontend/src/hooks/

// useProject.ts - Gerenciamento de projeto
export function useProject(projectId: string) {
  return useQuery({
    queryKey: ['project', projectId],
    queryFn: () => api.getProject(projectId),
  });
}

// useElements.ts - Árvore de elementos
export function useElements(projectId: string) {
  return useQuery({
    queryKey: ['elements', projectId],
    queryFn: () => api.getElements(projectId),
  });
}

// useChat.ts - Chat com streaming
export function useChat(projectId: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  
  const sendMessage = useCallback(async (content: string) => {
    setIsStreaming(true);
    // WebSocket streaming logic
  }, []);
  
  return { messages, sendMessage, isStreaming };
}

// useTokenUsage.ts - Métricas de consumo
export function useTokenUsage(projectId: string) {
  return useQuery({
    queryKey: ['tokenUsage', projectId],
    queryFn: () => api.getTokenUsage(projectId),
    refetchInterval: 30000, // Atualiza a cada 30s
  });
}

// useChange.ts - OpenSpec Change
export function useChange(changeId: string) {
  return useQuery({
    queryKey: ['change', changeId],
    queryFn: () => api.getChange(changeId),
  });
}

// useActiveChange.ts - Change ativa do projeto
export function useActiveChange(projectId: string) {
  return useQuery({
    queryKey: ['activeChange', projectId],
    queryFn: () => api.getActiveChange(projectId),
  });
}
```

### WebSocket para Streaming

```typescript
// frontend/src/lib/websocket.ts

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private projectId: string;
  
  constructor(projectId: string) {
    this.projectId = projectId;
  }
  
  connect(onMessage: (data: StreamMessage) => void) {
    this.ws = new WebSocket(
      `${process.env.NEXT_PUBLIC_WS_URL}/ws/chat/${this.projectId}`
    );
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };
  }
  
  send(message: string, context?: ChatContext) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ message, context }));
    }
  }
  
  disconnect() {
    this.ws?.close();
  }
}
```

---

## Funcionalidades Principais

### 1. Gestão de Projetos

**Dashboard de Projetos**
- Lista de todos os projetos do usuário com status (ativo, em conversão, concluído)
- Cards visuais com preview do projeto e progresso de conversão
- Filtros por status, data de criação, tecnologia de origem

**Criação de Projeto**
1. Upload de arquivo `.zip` contendo o projeto legado (wwp/wdp)
2. Validação e parsing automático dos metadados
3. Extração e indexação da estrutura de elementos
4. Criação do container Docker isolado para o tenant

---

### 2. Visão do Projeto Importado

Ao acessar um projeto, o usuário encontra um **menu lateral esquerdo** com as seguintes opções:

| Seção | Descrição |
|-------|-----------|
| 📊 **Visão Projeto Importado** | Árvore de elementos + Grafo de dependências |
| 🔄 **Conversões** | Histórico e status das conversões realizadas |
| 📝 **Changes** | OpenSpec Changes (ativa e arquivadas) |
| 💬 **Chat de Conversão** | Interface de comando assistido |
| ⚙️ **Configurações** | Settings do projeto e stack alvo |

#### 2.1 Árvore de Elementos

A árvore deve exibir os elementos **na mesma ordem** em que aparecem no arquivo principal do projeto (`.wwp` ou `.wdp`):

```
📁 Projeto Legado
├── 📄 Janelas (Windows)
│   ├── WIN_Principal
│   ├── WIN_Cadastro_Cliente
│   └── WIN_Relatorios
├── 📄 Páginas (Pages)
│   ├── PAGE_Home
│   └── PAGE_Login
├── 📄 Consultas (Queries)
│   ├── QRY_Clientes_Ativos
│   └── QRY_Vendas_Periodo
├── 📄 Classes
│   ├── CLS_Cliente
│   └── CLS_Pedido
├── 📄 Procedimentos Globais
│   ├── PROC_Validacao
│   └── PROC_Calculo_Impostos
└── 📄 Análise (Database)
    ├── TBL_Clientes
    └── TBL_Pedidos
```

**Interações da Árvore:**
- Clique em elemento → Exibe código fonte e metadados
- Checkbox de seleção → Marca elementos para conversão em lote
- Ícones de status → Indica se já foi convertido, pendente ou com erro
- Drag & drop → Reordenar prioridade de conversão

#### 2.2 Grafo de Dependências

Visualização interativa (usando D3.js ou similar) mostrando:
- **Nós**: Elementos do projeto (janelas, páginas, queries, classes)
- **Arestas**: Dependências entre elementos (chamadas, imports, referências)
- **Cores**: Status de conversão (verde=convertido, amarelo=pendente, vermelho=erro)
- **Clusters**: Agrupamento por módulo/funcionalidade

**Metadados Exibidos:**
- Quantidade de linhas de código por elemento
- Complexidade ciclomática estimada
- Quantidade de dependências (in/out)
- Tecnologias utilizadas (SQL, HTTP, arquivos)

---

### 3. Chat de Conversão com Guardrail

O workflow de conversão acontece via **interface de chat** que abstrai o Claude Code.

#### 3.1 Arquitetura do Guardrail

```
┌─────────────────────────────────────────────────────────────┐
│                    Chat UI (Next.js)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    GUARDRAIL LAYER                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 1. Sanitização de Input                                 ││
│  │    - Bloqueia comandos slash (/exit, /clear, etc)       ││
│  │    - Detecta e bloqueia prompt injection                ││
│  │    - Valida contexto do projeto                         ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ 2. Transformação de Comando                             ││
│  │    - Converte intenção do usuário em comandos seguros   ││
│  │    - Injeta contexto do projeto automaticamente         ││
│  │    - Limita escopo de operações permitidas              ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ 3. Filtragem de Output                                  ││
│  │    - Remove referências ao Claude Code                  ││
│  │    - Sanitiza paths e informações sensíveis             ││
│  │    - Formata resposta para o usuário                    ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Claude Code Bridge (Execução)                   │
│  docker exec claude-{tenant} claude -p "prompt"             │
│    --output-format stream-json                               │
│    --allowedTools "Read,Write,Edit,Bash(npm:*)"             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Token Tracker (Métricas)                        │
│  - Extrai usage de cada mensagem assistant                   │
│  - Registra total_cost_usd no banco                         │
│  - Atualiza dashboard em tempo real                          │
└─────────────────────────────────────────────────────────────┘
```

#### 3.2 Claude Code Bridge (Backend)

```python
# services/claude_bridge.py
import asyncio
import json
from typing import AsyncGenerator, Optional
import docker

class ClaudeCodeBridge:
    """Ponte de comunicação com Claude Code em containers Docker"""
    
    def __init__(self, tenant_id: str, token_tracker: TokenTracker):
        self.tenant_id = tenant_id
        self.container_name = f"claude-{tenant_id}"
        self.docker_client = docker.from_env()
        self.token_tracker = token_tracker
    
    async def execute(
        self, 
        prompt: str, 
        project_id: str,
        session_id: Optional[str] = None,
        allowed_tools: list = None,
        stream: bool = True
    ) -> AsyncGenerator[dict, None]:
        """Executa comando no Claude Code e retorna stream de respostas"""
        
        # Monta comando
        cmd = [
            "claude", "-p", prompt,
            "--output-format", "stream-json"
        ]
        
        # Continua sessão existente
        if session_id:
            cmd.extend(["--resume", session_id])
        
        # Ferramentas permitidas (restritivas por padrão)
        tools = allowed_tools or ["Read", "Write", "Edit", "Bash(npm:*)"]
        cmd.extend(["--allowedTools", ",".join(tools)])
        
        # Executa no container
        container = self.docker_client.containers.get(self.container_name)
        exec_result = container.exec_run(
            cmd,
            stream=True,
            workdir=f"/workspace/{project_id}"
        )
        
        # Processa stream
        for chunk in exec_result.output:
            for line in chunk.decode().strip().split('\n'):
                if line:
                    # Extrai métricas de tokens
                    parsed = self.token_tracker.process_stream_line(line)
                    if parsed:
                        yield parsed
        
        # Salva métricas da sessão
        self.token_tracker.save_usage(
            tenant_id=self.tenant_id,
            project_id=project_id,
            session_id=session_id
        )
```

#### 3.3 Guardrail Implementation

```python
# services/guardrail.py
import re
from typing import Tuple, List

class Guardrail:
    """Camada de segurança entre usuário e Claude Code"""
    
    # Padrões bloqueados no input
    BLOCKED_INPUT_PATTERNS = [
        r"^/\w+",                           # Comandos slash
        r"ignore\s+(previous|above)",       # Prompt injection
        r"system\s*prompt",                 # Tentativa de ver system prompt
        r"you\s+are\s+(now|a)",             # Roleplay injection
        r"ANTHROPIC_API_KEY",               # Leak de credenciais
        r"\.credentials\.json",             # Arquivo de credenciais
        r"rm\s+-rf",                        # Comandos destrutivos
        r"sudo\s+",                         # Elevação de privilégio
    ]
    
    # Padrões removidos do output
    OUTPUT_SANITIZE_PATTERNS = [
        (r"claude\s+-p", "[assistant]"),                    # Oculta claude-code
        (r"/home/claude/\.claude", "[config]"),             # Oculta paths internos
        (r"sk-ant-\w+", "[token]"),                         # Oculta tokens
        (r"/workspace/\w+/", ""),                           # Simplifica paths
    ]
    
    # Ferramentas permitidas por contexto
    ALLOWED_TOOLS_BY_CONTEXT = {
        "analysis": ["Read", "Grep", "Glob"],
        "conversion": ["Read", "Write", "Edit", "Bash(npm:*)"],
        "review": ["Read", "Grep"],
    }
    
    @classmethod
    def validate_input(cls, message: str) -> Tuple[bool, str]:
        """Valida mensagem do usuário antes de enviar ao Claude Code"""
        message_lower = message.lower()
        
        for pattern in cls.BLOCKED_INPUT_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return False, f"Comando não permitido"
        
        # Limite de tamanho
        if len(message) > 10000:
            return False, "Mensagem muito longa (máx 10.000 caracteres)"
        
        return True, ""
    
    @classmethod
    def sanitize_output(cls, output: dict) -> dict:
        """Remove informações sensíveis do output"""
        if "result" in output:
            result = output["result"]
            for pattern, replacement in cls.OUTPUT_SANITIZE_PATTERNS:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            output["result"] = result
        
        # Remove campos internos
        output.pop("session_id", None)  # Oculta session_id real
        
        return output
    
    @classmethod
    def get_allowed_tools(cls, context: str) -> List[str]:
        """Retorna ferramentas permitidas para o contexto"""
        return cls.ALLOWED_TOOLS_BY_CONTEXT.get(context, ["Read"])
```

#### 3.4 Funcionalidades do Chat

**O que o usuário pode fazer:**
- Pedir análise de um elemento específico
- Solicitar sugestão de sequência de conversão
- Iniciar conversão de elemento(s) selecionado(s)
- Perguntar sobre dependências e impactos
- Revisar e aprovar Changes geradas
- Visualizar consumo de tokens da sessão atual

**O que o Guardrail bloqueia:**
- Comandos slash (`/exit`, `/clear`, `/help`, etc)
- Tentativas de prompt injection
- Acesso a arquivos fora do escopo do projeto
- Comandos de sistema operacional diretos
- Referências ou manipulação do Claude Code em si

---

### 4. Sistema de OpenSpec Changes

Cada conversão gera uma **OpenSpec Change** que segue o workflow definido.

#### 4.1 Regra de Exclusividade

> ⚠️ **IMPORTANTE**: Cada projeto só pode ter **UMA Change aberta por vez**.  
> Uma nova Change só pode ser criada após a Change atual ser **arquivada** (aprovada ou rejeitada).

#### 4.2 Ciclo de Vida da Change

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  DRAFT   │───▶│  REVIEW  │───▶│ APPROVED │───▶│ ARCHIVED │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                     │                               ▲
                     │          ┌──────────┐        │
                     └─────────▶│ REJECTED │────────┘
                                └──────────┘
```

#### 4.3 UI da Change

**Painel de Change Ativa:**
- Header com título e status da Change
- Diff viewer com código antes/depois
- Lista de arquivos afetados
- Botões de ação: Aprovar, Rejeitar, Editar, Comentar

**Histórico de Changes:**
- Timeline de todas as Changes do projeto
- Filtros por status, elemento, data
- Busca por conteúdo da Change

---

### 5. Sugestão de Sequência de Conversão

O sistema deve **analisar o grafo de dependências** e sugerir a ordem ideal de conversão:

#### 5.1 Algoritmo de Priorização

1. **Elementos folha** (sem dependências) → Converter primeiro
2. **Elementos core/shared** (muito referenciados) → Converter cedo para desbloquear outros
3. **Clusters independentes** → Podem ser convertidos em paralelo
4. **Elementos com alta complexidade** → Priorizar para identificar problemas cedo

#### 5.2 UI de Sugestão

```
┌─────────────────────────────────────────────────────────────┐
│  📋 Sequência Sugerida de Conversão                         │
├─────────────────────────────────────────────────────────────┤
│  1. 🟢 CLS_Cliente (0 deps, core)           [Converter]     │
│  2. 🟢 CLS_Pedido (1 dep: CLS_Cliente)      [Converter]     │
│  3. 🟡 QRY_Clientes_Ativos (2 deps)         [Converter]     │
│  4. 🟡 WIN_Cadastro_Cliente (3 deps)        [Converter]     │
│  5. 🔴 WIN_Principal (8 deps)               [Bloqueado]     │
├─────────────────────────────────────────────────────────────┤
│  💡 Recomendação: Converter itens 1-4 antes de WIN_Principal│
│     para minimizar retrabalho.                              │
└─────────────────────────────────────────────────────────────┘
```

**Interações:**
- Aceitar sequência sugerida → Inicia conversão automática em fila
- Reordenar manualmente → Arrastar elementos na lista
- Converter individual → Botão por elemento
- Ver justificativa → Tooltip explicando a priorização

---

## Páginas Principais

### 1. Dashboard (`/dashboard`)

Visão geral de todos os projetos do usuário:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  WXCODE                                        [+ Novo Projeto]  👤  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  📊 Seus Projetos                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ 🏢 ERP-Vendas   │  │ 📦 Estoque-WD   │  │ ➕              │         │
│  │ ████████░░ 78%  │  │ ██░░░░░░░░ 15%  │  │                 │         │
│  │ 45/58 elementos │  │ 12/80 elementos │  │  Novo Projeto   │         │
│  │ Última: 2h atrás│  │ Última: 1 semana│  │                 │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                         │
│  📈 Consumo de Tokens (7 dias)                                          │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  [Gráfico de barras com consumo diário]                     │       │
│  │  Total: 245.8k tokens | Custo estimado: $12.47              │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. Workspace do Projeto (`/project/[id]`)

Interface principal inspirada no Lovable/Replit com painéis redimensionáveis:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  WXCODE > ERP-Vendas                    [▶ Converter] [⚙️] [📊]     │
├──────────────────────┬──────────────────────────────────────────────────┤
│  📁 Elementos        │  ┌─────────────────────────────────────────────┐ │
│  ├── 📄 Janelas      │  │  Monaco Editor                              │ │
│  │   ├── WIN_Principal│  │  ─────────────────────────────────────────  │ │
│  │   ├── WIN_Cadastro │  │  PROCEDURE Principal()                     │ │
│  │   └── WIN_Relatorio│  │    HOpenConnection(MinhaConexao)           │ │
│  ├── 📄 Páginas      │  │    TableDisplay(TBL_Clientes)               │ │
│  │   ├── PAGE_Home   │  │  END                                        │ │
│  │   └── PAGE_Login  │  │                                             │ │
│  ├── 📄 Classes      │  └─────────────────────────────────────────────┘ │
│  │   ├── CLS_Cliente │  ┌─────────────────────────────────────────────┐ │
│  │   └── CLS_Pedido  │  │  💬 Chat de Conversão                       │ │
│  └── 📄 Queries      │  │  ─────────────────────────────────────────  │ │
│      ├── QRY_Vendas  │  │  🤖 Analisei WIN_Principal. Encontrei 3     │ │
│      └── QRY_Clientes│  │     dependências: CLS_Cliente, QRY_Vendas,  │ │
│                      │  │     e conexão MinhaConexao.                 │ │
│  ────────────────────│  │                                             │ │
│  🔄 Change Ativa     │  │  👤 Converta para React + TypeScript        │ │
│  ┌────────────────┐  │  │                                             │ │
│  │ #42 Converter  │  │  │  🤖 Criando OpenSpec Change...              │ │
│  │ WIN_Principal  │  │  │     ████████░░░░ 67%                        │ │
│  │ ⏳ Em progresso│  │  │                                             │ │
│  └────────────────┘  │  │  [Digite sua mensagem...]            [Enviar]│ │
│                      │  └─────────────────────────────────────────────┘ │
├──────────────────────┴──────────────────────────────────────────────────┤
│  🖥️ Terminal                                                    [─][□][×]│
│  $ claude -p "Convertendo WIN_Principal..." --output-format stream-json │
│  {"type":"assistant","message":{"content":"Analisando estrutura..."}}   │
│  {"type":"assistant","usage":{"input_tokens":1234,"output_tokens":89}}  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3. Visualização de Grafo (`/project/[id]/graph`)

Grafo interativo de dependências usando React Flow:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📊 Grafo de Dependências                    [Zoom +][-] [Fit] [Export] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│         ┌─────────────┐                                                 │
│         │ 🟢 CLS_     │                                                 │
│         │   Cliente   │◄────────┐                                       │
│         └──────┬──────┘         │                                       │
│                │                │                                       │
│                ▼                │                                       │
│         ┌─────────────┐  ┌─────────────┐                               │
│         │ 🟡 QRY_     │  │ 🟡 CLS_     │                               │
│         │   Vendas    │  │   Pedido    │                               │
│         └──────┬──────┘  └──────┬──────┘                               │
│                │                │                                       │
│                └────────┬───────┘                                       │
│                         ▼                                               │
│                  ┌─────────────┐                                        │
│                  │ 🔴 WIN_     │                                        │
│                  │  Principal  │                                        │
│                  └─────────────┘                                        │
│                                                                         │
│  Legenda: 🟢 Convertido  🟡 Pendente  🔴 Bloqueado (deps pendentes)     │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  Nó selecionado: WIN_Principal                                          │
│  Dependências: 4 | Dependentes: 0 | Linhas: 342 | Complexidade: Alta    │
│  [Ver Código] [Iniciar Conversão] [Adicionar à Fila]                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4. Diff/Review de Changes (`/project/[id]/changes/[changeId]`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📝 Change #42: Converter WIN_Principal          [Aprovar] [Rejeitar]   │
├────────────────────────────────┬────────────────────────────────────────┤
│  WLanguage (Original)          │  TypeScript (Convertido)               │
├────────────────────────────────┼────────────────────────────────────────┤
│  PROCEDURE Principal()         │  export function Principal() {         │
│    HOpenConnection(MinhaConexao│    const db = useDatabase();           │
│    TableDisplay(TBL_Clientes)  │    const { data } = useQuery('clients')│
│  END                           │    return <ClientTable data={data} />  │
│                                │  }                                     │
├────────────────────────────────┴────────────────────────────────────────┤
│  📊 Métricas da Conversão                                               │
│  Tokens: 2,345 input | 892 output | Cache: 1,200 | Custo: $0.12        │
│  Tempo: 45s | Modelo: claude-sonnet-4-20250514                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Diretrizes de Design (claude-design-skill)

### Estética Geral

**Direção**: **IDE Moderna** inspirada em Lovable/Replit + **Dark Mode Premium**

- Interface focada em produtividade com painéis redimensionáveis
- Dark mode como padrão (desenvolvedores preferem)
- Tipografia monospace para código (JetBrains Mono, Fira Code)
- Tipografia sans-serif para UI (Inter, Geist Sans)
- Paleta de cores com alto contraste para status (verde/amarelo/vermelho)
- Espaçamento generoso para reduzir fadiga visual
- Animações sutis mas responsivas

### Paleta de Cores (Dark Mode)

```css
:root {
  /* Background */
  --bg-primary: #0a0a0b;
  --bg-secondary: #141415;
  --bg-tertiary: #1c1c1e;
  
  /* Text */
  --text-primary: #fafafa;
  --text-secondary: #a1a1aa;
  --text-muted: #71717a;
  
  /* Accent */
  --accent-primary: #3b82f6;    /* Blue */
  --accent-success: #22c55e;    /* Green - Convertido */
  --accent-warning: #eab308;    /* Yellow - Pendente */
  --accent-error: #ef4444;      /* Red - Erro/Bloqueado */
  
  /* Borders */
  --border-subtle: #27272a;
  --border-default: #3f3f46;
}
```

### Componentes Chave

**Árvore de Elementos (Sidebar):**
- Indentação clara com linhas de conexão
- Ícones distintivos por tipo de elemento (shadcn/ui icons)
- Hover effects sutis
- Drag & drop para reordenar
- Context menu (right-click)

**Monaco Editor:**
- Syntax highlighting customizado para WLanguage
- Minimap opcional
- Diff view side-by-side
- Breadcrumbs de navegação

**React Flow (Grafo):**
- Layout force-directed com física suave
- Zoom e pan fluidos (controls visíveis)
- Highlighting de path ao selecionar nó
- Minimap para navegação
- Custom nodes com status visual

**XTerm.js (Terminal):**
- Tema consistente com a UI
- Scrollback buffer
- Copy/paste funcional
- Resize automático

**Chat Interface:**
- Bubbles com diferenciação clara user/assistant
- Syntax highlighting inline para código
- Indicador de loading/streaming
- Typing indicator durante processamento
- Auto-scroll para novas mensagens

---

## Stack Tecnológico

| Camada | Tecnologia | Motivo |
|--------|------------|--------|
| **Framework** | Next.js 14+ (App Router) | Server Components, API Routes, SSR |
| **Styling** | TailwindCSS + shadcn/ui | Componentes prontos, consistente, dark mode |
| **Editor** | Monaco Editor | Mesmo do VS Code, syntax highlighting WLanguage |
| **Grafos** | React Flow | Visualização de dependências interativa |
| **Terminal** | XTerm.js | Terminal real no browser |
| **State** | TanStack Query | Cache, sync com backend, mutations |
| **Realtime** | WebSockets | Atualizações de status ao vivo |
| **Deploy** | Docker self-hosted | Controle total, sem vendor lock-in |

### Docker Compose Completo

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    networks:
      - wx-network

  backend:
    build: ./src
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongodb:27017
      - NEO4J_URI=bolt://neo4j:7687
    depends_on:
      - mongodb
      - neo4j
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Para gerenciar containers dos tenants
    networks:
      - wx-network

  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    networks:
      - wx-network

  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - neo4j_data:/data
    networks:
      - wx-network

volumes:
  mongodb_data:
  neo4j_data:
  claude-credentials:

networks:
  wx-network:
    driver: bridge
```

### Dockerfile do Frontend (Next.js)

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
```

---

## Referências

- **Chat anterior**: [Claude Code em Docker com autenticação por assinatura](https://claude.ai/chat/680cb76e-6f52-41e8-b382-b300bf2daf7b) - Discussão sobre arquitetura de autenticação OAuth e Guardrail
- **Claude Code Headless**: https://code.claude.com/docs/en/headless - Documentação oficial do modo programático
- **Output Format stream-json**: Formato que inclui métricas de tokens em tempo real
- **Inspiração UI**: Lovable.dev e Replit - IDEs web modernas com chat integrado

---

## Próximos Passos

### Fase 1: Setup Inicial
1. [ ] Criar estrutura `frontend/` no monorepo wxcode
2. [ ] Configurar Next.js 14+ com App Router
3. [ ] Instalar e configurar shadcn/ui + TailwindCSS
4. [ ] Configurar TanStack Query
5. [ ] Criar Dockerfile para frontend

### Fase 2: Infraestrutura
6. [ ] **Implementar setup de autenticação OAuth** (script + volume Docker)
7. [ ] **Implementar Token Tracker** (parser de métricas + banco de dados)
8. [ ] Implementar Guardrail como módulo isolado
9. [ ] Configurar WebSocket para streaming
10. [ ] Criar API Routes proxy para FastAPI

### Fase 3: Componentes Core
11. [ ] Implementar layout com painéis redimensionáveis
12. [ ] Integrar Monaco Editor com syntax highlighting WLanguage
13. [ ] Integrar React Flow para grafo de dependências
14. [ ] Integrar XTerm.js para terminal
15. [ ] Implementar Chat Interface com streaming

### Fase 4: Features
16. [ ] Prototipar UI da Árvore de Elementos
17. [ ] **Criar dashboard de consumo de tokens**
18. [ ] Implementar sistema de OpenSpec Changes
19. [ ] Integrar com parser de arquivos .wwp/.wdp existente
20. [ ] Implementar API de limites de assinatura (5h/7d)

### Fase 5: Polish
21. [ ] Implementar dark mode premium
22. [ ] Adicionar animações e transições
23. [ ] Testes e otimizações de performance
24. [ ] Documentação de uso
