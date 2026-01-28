# Tasks: frontend-infrastructure

## Task 1: Criar modelo TokenUsageLog

**File:** `src/wxcode/models/token_usage.py`

**Steps:**
1. Criar arquivo com model Beanie TokenUsageLog
2. Incluir campos: tenant_id, project_id, session_id, métricas de tokens, custo
3. Configurar indexes para queries eficientes

**Acceptance Criteria:**
- [x] Model TokenUsageLog criado com Beanie
- [x] Campos de tokens: input, output, cache_creation, cache_read
- [x] Campo total_cost_usd para custo
- [x] Index composto em (tenant_id, project_id)

---

## Task 2: Criar TokenTracker service

**File:** `src/wxcode/services/token_tracker.py`

**Steps:**
1. Criar classe TokenTracker
2. Implementar process_stream_line() para extrair métricas do JSON
3. Implementar save_usage() para persistir no MongoDB

**Acceptance Criteria:**
- [x] TokenTracker processa linhas stream-json
- [x] Extrai usage de mensagens type=assistant
- [x] Extrai total_cost_usd do resultado final
- [x] Persiste TokenUsageLog no MongoDB

---

## Task 3: Criar Guardrail service

**File:** `src/wxcode/services/guardrail.py`

**Steps:**
1. Criar classe Guardrail com padrões bloqueados
2. Implementar validate_input() para sanitização de entrada
3. Implementar sanitize_output() para filtrar dados sensíveis
4. Implementar get_allowed_tools() por contexto

**Acceptance Criteria:**
- [x] Bloqueia comandos slash (/exit, /clear)
- [x] Bloqueia padrões de prompt injection
- [x] Sanitiza paths e tokens no output
- [x] Retorna ferramentas permitidas por contexto

---

## Task 4: Criar ClaudeBridge service

**File:** `src/wxcode/services/claude_bridge.py`

**Steps:**
1. Criar classe ClaudeBridge
2. Implementar execute() async generator para stream
3. Integrar com TokenTracker para métricas

**Acceptance Criteria:**
- [x] ClaudeBridge executa comandos em containers Docker
- [x] Retorna stream de respostas via async generator
- [x] Integra TokenTracker para rastrear uso

---

## Task 5: Criar WebSocket endpoint

**File:** `src/wxcode/api/websocket.py`

**Steps:**
1. Criar router WebSocket com FastAPI
2. Implementar handler de conexão e mensagens
3. Integrar Guardrail e ClaudeBridge

**Acceptance Criteria:**
- [x] Endpoint WS /ws/chat/{project_id}
- [x] Valida input via Guardrail antes de executar
- [x] Stream de respostas para cliente
- [x] Envia métricas de tokens ao final

---

## Task 6: Criar API Routes proxy no Next.js

**File:** `frontend/src/app/api/[...path]/route.ts`

**Steps:**
1. Criar catch-all route handler
2. Implementar proxy para backend FastAPI
3. Passar headers de autenticação

**Acceptance Criteria:**
- [x] Route handler para /api/*
- [x] Proxy requests para NEXT_PUBLIC_API_URL
- [x] Suporte a GET, POST, PUT, DELETE

---

## Task 7: Criar lib WebSocket client

**File:** `frontend/src/lib/websocket.ts`

**Steps:**
1. Criar classe ChatWebSocket
2. Implementar connect(), send(), disconnect()
3. Tipagem TypeScript para mensagens

**Acceptance Criteria:**
- [x] ChatWebSocket class funcional
- [x] Métodos connect/send/disconnect
- [x] Tipos StreamMessage e ChatContext

---

## Task 8: Criar hook useChat

**File:** `frontend/src/hooks/useChat.ts`

**Steps:**
1. Criar hook com estado de mensagens
2. Integrar ChatWebSocket
3. Expor sendMessage() e estado isStreaming

**Acceptance Criteria:**
- [x] Hook useChat(projectId)
- [x] Estado: messages, isStreaming
- [x] Função sendMessage() com streaming

---

## Task 9: Criar hook useTokenUsage

**File:** `frontend/src/hooks/useTokenUsage.ts`

**Steps:**
1. Criar hook com TanStack Query
2. Fetch de métricas do backend
3. Refetch automático a cada 30s

**Acceptance Criteria:**
- [x] Hook useTokenUsage(projectId)
- [x] Retorna métricas de tokens
- [x] Atualiza automaticamente

---

## Task 10: Criar script setup-auth.sh

**File:** `scripts/setup-auth.sh`

**Steps:**
1. Criar script de setup de credenciais
2. Criar volume Docker para credenciais
3. Executar claude login interativamente

**Acceptance Criteria:**
- [x] Script cria volume claude-credentials
- [x] Executa claude login em container
- [x] Credenciais persistidas no volume

---

## Task 11: Atualizar docker-compose.yml

**File:** `docker-compose.yml`

**Steps:**
1. Adicionar serviço claude-worker
2. Referenciar volume claude-credentials como external
3. Configurar networks

**Acceptance Criteria:**
- [x] Serviço claude-worker configurado
- [x] Volume claude-credentials referenciado
- [x] Conectado à wx-network

---

## Dependencies

```
Task 1 → Task 2 → Task 4 → Task 5 (sequencial backend)
Task 3 → Task 5 (guardrail antes de websocket)
Task 6 → Task 7 → Task 8, Task 9 (sequencial frontend)
Task 10 → Task 11 (sequencial docker)
```

## Validation Commands

```bash
# Após Tasks 1-5
cd /Users/gilberto/projetos/wxk/wxcode
PYTHONPATH=src python -c "from wxcode.services.guardrail import Guardrail; print(Guardrail.validate_input('test'))"

# Após Tasks 6-9
cd frontend && npm run build

# Após Tasks 10-11
./scripts/setup-auth.sh  # Interativo
docker compose config --services | grep claude
```

## Summary

All 11 tasks completed successfully. Infrastructure is ready for Phase 3 (components).
