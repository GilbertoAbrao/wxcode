# Tasks: Implement Chat AI Agent

> 💡 Recomendação: Use **Sonnet 4.5** para estas tasks (isoladas, um arquivo por task)

---

## Task 1: Criar MessageType enum e MessageClassifier

**File:** `src/wxcode/services/message_classifier.py`

**Steps:**
1. Criar arquivo com enum `MessageType` (question, multi_question, info, tool_result, error, thinking)
2. Criar classe `MessageClassifier` com método `classify(json_data: dict) -> MessageType`
3. Implementar heurísticas de classificação via regex pré-compilados
4. Adicionar docstrings

**Acceptance Criteria:**
- [x] Arquivo existe em `src/wxcode/services/message_classifier.py`
- [x] `MessageType` enum com 6 valores
- [x] `classify()` retorna tipo correto para: pergunta simples, multi-question, tool_result
- [x] Regex patterns são pré-compilados (performance)

---

## Task 2: Criar OutputSanitizer

**File:** `src/wxcode/services/output_sanitizer.py`

**Steps:**
1. Criar arquivo com classe `OutputSanitizer`
2. Definir `CLI_PATTERNS` para sanitizar referências (claude-code, codex, gpt, anthropic, openai)
3. Definir `INTERNAL_PATTERNS` para remover detalhes técnicos (tool_use_id, MCP, etc.)
4. Implementar método `sanitize(content: str) -> str`

**Acceptance Criteria:**
- [x] Arquivo existe em `src/wxcode/services/output_sanitizer.py`
- [x] Sanitiza "claude-code" → "[assistant]"
- [x] Sanitiza "anthropic" → "[provider]"
- [x] Remove tool_use_id e padrões internos
- [x] Regex pré-compilados

---

## Task 3: Estender Guardrail com padrões de injection

**File:** `src/wxcode/services/guardrail.py`

**Steps:**
1. Adicionar novos padrões em `BLOCKED_INPUT_PATTERNS`:
   - Jailbreak: "DAN mode", "developer mode"
   - Roleplay: "pretend you", "act as if"
   - Override: "new instructions:", "forget everything"
   - Code exec: `exec(`, `__import__`, `os.system`
2. Adicionar teste inline para verificar padrões

**Acceptance Criteria:**
- [x] `BLOCKED_INPUT_PATTERNS` contém pelo menos 8 novos padrões
- [x] Padrões detectam "DAN mode enabled"
- [x] Padrões detectam "forget all previous instructions"
- [x] Não bloqueia mensagens normais como "Can you help me?"

---

## Task 4: Criar ChatAgent orquestrador

**File:** `src/wxcode/services/chat_agent.py`

**Steps:**
1. Criar arquivo com classe `ChatAgent`
2. Importar `MessageClassifier`, `OutputSanitizer`, `Guardrail`
3. Implementar `process_input(message: str) -> ProcessedInput`
4. Implementar `process_output(json_data: dict) -> ProcessedMessage`
5. Criar dataclasses `ProcessedInput` e `ProcessedMessage`

**Acceptance Criteria:**
- [x] Arquivo existe em `src/wxcode/services/chat_agent.py`
- [x] `ProcessedInput` tem campos: valid, error, cleaned
- [x] `ProcessedMessage` tem campos: type, content, options, metadata
- [x] `process_input` usa Guardrail.validate_input
- [x] `process_output` usa Classifier e Sanitizer

---

## Task 5: Integrar ChatAgent no WebSocket endpoint

**File:** `src/wxcode/api/websocket.py`

**Steps:**
1. Importar `ChatAgent` de services
2. Instanciar ChatAgent no handler WebSocket
3. Usar `agent.process_input()` antes de enviar ao Claude
4. Usar `agent.process_output()` para processar cada mensagem JSON
5. Enviar mensagem processada com `type` correto

**Acceptance Criteria:**
- [x] Import de ChatAgent adicionado
- [x] Input é validado com process_input antes de execução
- [x] Output JSON é processado com process_output
- [x] Mensagens enviadas ao cliente incluem `type` do MessageType

---

## Task 6: Adicionar testes unitários

**File:** `tests/test_chat_agent.py`

**Steps:**
1. Criar arquivo de testes
2. Testar `MessageClassifier.classify()` com fixtures JSON
3. Testar `OutputSanitizer.sanitize()` com strings de teste
4. Testar `Guardrail.validate_input()` com injection attempts
5. Testar `ChatAgent` end-to-end

**Acceptance Criteria:**
- [x] Arquivo existe em `tests/test_chat_agent.py`
- [x] >= 10 test cases cobrindo classificação (26 testes)
- [x] >= 5 test cases cobrindo sanitização (14 testes)
- [x] >= 5 test cases cobrindo injection detection (15 testes)
- [x] Todos os testes passam (66 total)

---

## Task 7: Atualizar frontend para tipos de mensagem

**File:** `frontend/src/hooks/useChat.ts`

**Steps:**
1. Adicionar type para `MessageType` no TypeScript
2. Atualizar handler `onMessage` para processar `type`
3. Mapear tipos para comportamentos de UI

**Acceptance Criteria:**
- [x] Type `MessageType` definido em TypeScript
- [x] Hook processa mensagens com base no `type`
- [x] Mensagens `question` focam input automaticamente (via isAwaitingResponse)

---

## Task 8: Atualizar ChatMessage para renderizar por tipo

**File:** `frontend/src/components/chat/ChatMessage.tsx`

**Steps:**
1. Adicionar prop `messageType` ao componente
2. Renderizar perguntas com estilo diferenciado
3. Renderizar `multi_question` com botões de opção
4. Renderizar `tool_result` de forma colapsável

**Acceptance Criteria:**
- [x] Componente aceita `messageType` prop
- [x] Perguntas têm estilo visual distinto (purple styling)
- [x] Multi-question renderiza opções como botões
- [x] Tool results são colapsáveis

---

## Dependency Graph

```
Task 1 (Classifier) ──┐
Task 2 (Sanitizer) ───┼──▶ Task 4 (ChatAgent) ──▶ Task 5 (WebSocket)
Task 3 (Guardrail) ───┘                              │
                                                     ▼
                                              Task 6 (Tests)
                                                     │
Task 7 (useChat) ────────────────────────────────────┘
        │
        ▼
Task 8 (ChatMessage)
```

**Parallelizable:** Tasks 1, 2, 3 podem ser feitas em paralelo.
**Sequential:** Task 4 depende de 1-3. Task 5 depende de 4. Tasks 7-8 dependem de 5.
