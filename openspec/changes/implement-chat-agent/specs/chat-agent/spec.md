# Spec Delta: chat-agent

## Overview
Capability para processamento inteligente de mensagens de chat entre usuário e Claude Code.

---

## ADDED Requirements

### Requirement: Message Classification
The system MUST classify JSON messages from Claude Code into semantic types.

#### Scenario: Classificar pergunta simples
- **Given** uma mensagem JSON com texto terminando em "?"
- **When** o MessageClassifier processa a mensagem
- **Then** retorna `MessageType.QUESTION`

#### Scenario: Classificar múltiplas perguntas
- **Given** uma mensagem JSON contendo array de opções ou estrutura AskUserQuestion
- **When** o MessageClassifier processa a mensagem
- **Then** retorna `MessageType.MULTI_QUESTION`

#### Scenario: Classificar resultado de ferramenta
- **Given** uma mensagem JSON com type="tool_result" ou contendo tool_use
- **When** o MessageClassifier processa a mensagem
- **Then** retorna `MessageType.TOOL_RESULT`

#### Scenario: Classificar erro
- **Given** uma mensagem JSON com type="error" ou indicadores de falha
- **When** o MessageClassifier processa a mensagem
- **Then** retorna `MessageType.ERROR`

#### Scenario: Fallback para informação
- **Given** uma mensagem JSON que não se encaixa em outros tipos
- **When** o MessageClassifier processa a mensagem
- **Then** retorna `MessageType.INFO`

---

### Requirement: CLI Reference Sanitization
The system MUST remove references to the underlying CLI from messages.

#### Scenario: Sanitizar referência a Claude Code
- **Given** texto contendo "claude-code" ou "Claude Code"
- **When** o OutputSanitizer processa o texto
- **Then** substitui por "[assistant]"

#### Scenario: Sanitizar referência a outras CLIs
- **Given** texto contendo "Codex", "GPT-4", ou similar
- **When** o OutputSanitizer processa o texto
- **Then** substitui por "[assistant]"

#### Scenario: Sanitizar referência a providers
- **Given** texto contendo "Anthropic", "OpenAI"
- **When** o OutputSanitizer processa o texto
- **Then** substitui por "[provider]"

#### Scenario: Remover detalhes técnicos internos
- **Given** texto contendo tool_use_id, MCP server, ou flags de CLI
- **When** o OutputSanitizer processa o texto
- **Then** remove completamente esses padrões

---

### Requirement: Prompt Injection Detection
The system MUST detect and block prompt injection attempts.

#### Scenario: Bloquear jailbreak DAN mode
- **Given** input contendo "DAN mode" ou "developer mode"
- **When** o Guardrail valida o input
- **Then** retorna (False, "Comando não permitido")

#### Scenario: Bloquear roleplay manipulation
- **Given** input contendo "pretend you are" ou "act as if"
- **When** o Guardrail valida o input
- **Then** retorna (False, "Comando não permitido")

#### Scenario: Bloquear instruction override
- **Given** input contendo "new instructions:" ou "forget everything"
- **When** o Guardrail valida o input
- **Then** retorna (False, "Comando não permitido")

#### Scenario: Bloquear code execution
- **Given** input contendo "exec(", "__import__", ou "os.system"
- **When** o Guardrail valida o input
- **Then** retorna (False, "Comando não permitido")

#### Scenario: Permitir mensagens legítimas
- **Given** input contendo "Can you help me understand this code?"
- **When** o Guardrail valida o input
- **Then** retorna (True, "")

---

### Requirement: Chat Agent Orchestration
The system MUST orchestrate classification, sanitization, and message formatting.

#### Scenario: Processar input válido
- **Given** uma mensagem de usuário válida
- **When** ChatAgent.process_input() é chamado
- **Then** retorna ProcessedInput com valid=True e cleaned=mensagem

#### Scenario: Processar input com injection
- **Given** uma mensagem de usuário contendo prompt injection
- **When** ChatAgent.process_input() é chamado
- **Then** retorna ProcessedInput com valid=False e error explicativo

#### Scenario: Processar output JSON
- **Given** um JSON de resposta do Claude Code
- **When** ChatAgent.process_output() é chamado
- **Then** retorna ProcessedMessage com type, content sanitizado, e options (se aplicável)

---

### Requirement: WebSocket Integration
The system MUST integrate ChatAgent into the existing WebSocket endpoint.

#### Scenario: Validar input antes de execução
- **Given** uma mensagem recebida via WebSocket
- **When** o handler processa a mensagem
- **Then** usa ChatAgent.process_input() antes de enviar ao Claude Code

#### Scenario: Processar output antes de envio
- **Given** uma resposta JSON do Claude Code
- **When** o handler prepara para enviar ao cliente
- **Then** usa ChatAgent.process_output() e envia mensagem processada

#### Scenario: Incluir tipo de mensagem na resposta
- **Given** uma mensagem processada pelo ChatAgent
- **When** enviada ao cliente via WebSocket
- **Then** inclui campo `type` com o MessageType correspondente

---

### Requirement: Frontend Message Rendering
The system MUST render messages according to their type.

#### Scenario: Renderizar pergunta
- **Given** uma mensagem com type="question"
- **When** o ChatMessage renderiza
- **Then** exibe com estilo visual de pergunta e foca no input

#### Scenario: Renderizar múltiplas opções
- **Given** uma mensagem com type="multi_question" e options
- **When** o ChatMessage renderiza
- **Then** exibe opções como botões clicáveis

#### Scenario: Renderizar resultado de ferramenta
- **Given** uma mensagem com type="tool_result"
- **When** o ChatMessage renderiza
- **Then** exibe em formato colapsável

#### Scenario: Renderizar erro
- **Given** uma mensagem com type="error"
- **When** o ChatMessage renderiza
- **Then** exibe com estilo visual de erro (vermelho)
