# Proposal: Implement Chat AI Agent

## Change ID
`implement-chat-agent`

## Summary
Implementar um Chat AI Agent que processa a saída JSON do Claude Code headless, identifica tipos de mensagem (pergunta, múltiplas perguntas, informação), sanitiza referências à CLI subjacente e detecta prompt injection de forma robusta.

## Motivation
Atualmente, o sistema exibe a saída raw do Claude Code no terminal, mas o chat precisa de um agente inteligente que:
1. **Interprete a estrutura JSON** do Claude Code para apresentar ao usuário de forma amigável
2. **Identifique tipos de mensagem** para adaptar a UI (perguntas precisam de input, informações são apenas display)
3. **Sanitize referências à CLI** para que o usuário não saiba qual ferramenta está rodando por trás (Claude-Code, Codex, etc.)
4. **Detecte prompt injection** e comandos maliciosos de forma mais robusta

## Goals
1. Criar `MessageClassifier` que categoriza mensagens em: `question`, `multi_question`, `info`, `tool_result`, `error`
2. Estender `Guardrail` com padrões adicionais de sanitização de CLI e prompt injection
3. Criar `ChatAgent` que orquestra classificação, sanitização e formatação
4. Integrar o agente no WebSocket de chat existente

## Non-Goals
- Não substituir o Claude Code por outro LLM
- Não criar um sistema de chat completamente novo (usar infraestrutura existente)
- Não implementar multi-tenancy ou isolamento de containers (já existe)

## Dependencies
- Guardrail existente (`src/wxcode/services/guardrail.py`)
- WebSocket endpoint (`src/wxcode/api/websocket.py`)
- Claude Bridge (`src/wxcode/services/claude_bridge.py`)
- GSD Invoker (`src/wxcode/services/gsd_invoker.py`)

## Spec Deltas
- **ADDED**: `chat-agent` - Nova capability para processamento inteligente de chat

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Falsos positivos no detector de injection | Lista whitelist para padrões comuns |
| Classificação errada de mensagens | Fallback para `info` em caso de dúvida |
| Performance do classificador | Usar regex pré-compilado, cache de padrões |

## Model Recommendation
**Sonnet 4.5** - Tasks isoladas, padrões claros, um arquivo por task.
