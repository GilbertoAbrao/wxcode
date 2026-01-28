# Proposal: frontend-infrastructure

## Summary

Implementar a infraestrutura de backend necessária para suportar o frontend wxcode, incluindo autenticação OAuth para containers Claude Code, sistema de tracking de tokens, camada de guardrail para segurança, WebSocket para streaming e API Routes proxy.

## Motivation

O frontend precisa de infraestrutura robusta para:
1. **Autenticar containers** - Claude Code em containers Docker isolados por tenant
2. **Rastrear consumo** - Métricas de tokens para billing e limites
3. **Garantir segurança** - Sanitização de inputs e outputs
4. **Streaming** - Respostas em tempo real via WebSocket
5. **Integração** - Proxy entre frontend Next.js e backend FastAPI

## Scope

### In Scope
- Script de setup de autenticação OAuth
- Volume Docker para credenciais
- TokenTracker service (parser + modelo Beanie)
- TokenUsageLog model MongoDB
- Guardrail service (validação + sanitização)
- WebSocket endpoint no FastAPI
- API Routes proxy no Next.js
- Hooks de useChat e useTokenUsage

### Out of Scope
- UI de dashboard de consumo (Fase 4)
- Componentes de chat (Fase 3)
- Multi-tenancy completo (simplificado nesta fase)
- Sistema de limites de assinatura (futuro)

## Dependencies

- `frontend-setup` (completed) - Next.js configurado
- FastAPI backend existente
- MongoDB configurado
- Docker compose funcional

## Related Specs

- `oauth-auth` - Autenticação Claude Code
- `token-tracker` - Rastreamento de tokens
- `guardrail` - Segurança e sanitização
- `websocket-streaming` - Streaming em tempo real
