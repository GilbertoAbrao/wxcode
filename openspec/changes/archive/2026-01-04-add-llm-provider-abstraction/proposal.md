# Proposal: add-llm-provider-abstraction

## Summary

Tornar o conversor LLM agnóstico de provider, permitindo uso de diferentes LLMs (Anthropic Claude, OpenAI GPT, Ollama local) através de uma abstração `LLMProvider`.

## Motivation

A implementação atual do `LLMClient` está fortemente acoplada à API da Anthropic:

1. **Vendor lock-in**: Usuários são forçados a usar Anthropic/Claude
2. **Custo**: Não há opção de usar modelos mais baratos (GPT-4o-mini) ou gratuitos (Ollama local)
3. **Disponibilidade**: Se Anthropic estiver fora, não há fallback
4. **Testes**: Difícil testar sem chamar API real

Com a abstração, usuários podem:
- Escolher o provider preferido
- Usar modelos locais para desenvolvimento (Ollama)
- Reduzir custos com modelos mais baratos
- Ter fallback automático entre providers

## Scope

### In Scope

- Criar protocol `LLMProvider` com interface comum
- Refatorar `LLMClient` atual para `AnthropicProvider`
- Implementar `OpenAIProvider` para GPT-4o/GPT-4o-mini
- Implementar `OllamaProvider` para modelos locais
- Criar factory `create_provider()` para instanciar providers
- Atualizar CLI com opção `--provider`
- Manter SYSTEM_PROMPT compartilhado entre providers

### Out of Scope

- Providers para outros serviços (Google Gemini, Mistral API, etc.)
- Streaming de respostas
- Fallback automático entre providers (pode ser adicionado depois)
- Cache de respostas por provider

## Design

Ver [design.md](./design.md) para arquitetura detalhada.

## Spec Deltas

| Spec | Type | Description |
|------|------|-------------|
| llm-provider | NEW | Define interface LLMProvider e implementações |

## Risks

1. **Qualidade variável**: Diferentes LLMs podem gerar código de qualidade diferente
   - Mitigação: Documentar modelos recomendados, validar output em todos
2. **Formatos de resposta**: Alguns modelos podem não seguir JSON estritamente
   - Mitigação: ResponseParser já lida com extração de JSON de markdown
3. **Custos ocultos**: OpenAI tem preços diferentes
   - Mitigação: Mostrar custo estimado por provider

## Success Criteria

- [ ] `wxcode convert-page PAGE_Login --provider anthropic` funciona
- [ ] `wxcode convert-page PAGE_Login --provider openai` funciona
- [ ] `wxcode convert-page PAGE_Login --provider ollama` funciona
- [ ] Todos os providers geram output válido para PAGE_Login
- [ ] Documentação atualizada com providers disponíveis
