# Proposal: frontend-features

## Summary

Implementar features de negócio do frontend: árvore de elementos, dashboard de tokens, sistema de conversões e páginas do projeto.

## Motivation

A Fase 3 entregou os componentes core (Editor, Graph, Terminal, Chat, Layout). Agora precisamos das features que conectam esses componentes em fluxos de trabalho úteis para o usuário.

## Scope

### In Scope

1. **ElementTree** - Navegação hierárquica de elementos do projeto
2. **TokenDashboard** - Visualização de consumo de tokens
3. **ConversionSystem** - UI para gerenciar conversões (OpenSpec changes abstraído)
4. **ProjectPages** - Dashboard, Workspace, Graph, Conversão

### Out of Scope

- Dark mode premium (Fase 5)
- Animações avançadas (Fase 5)
- Testes E2E (Fase 5)

## Design

Ver [design.md](./design.md) para arquitetura detalhada.

## Dependencies

- frontend-components (Fase 3) - Componentes base
- frontend-infrastructure (Fase 2) - Hooks e WebSocket

## Capabilities Affected

| Capability | Type | Description |
|------------|------|-------------|
| element-tree | ADDED | Navegação de elementos |
| token-dashboard | ADDED | Métricas de consumo |
| conversion-system | ADDED | Sistema de conversões |
| project-pages | ADDED | Páginas do projeto |
