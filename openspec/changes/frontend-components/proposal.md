# Proposal: frontend-components

## Summary

Implementar os componentes core da interface wxcode: Monaco Editor com syntax highlighting WLanguage, React Flow para visualização de grafo de dependências, XTerm.js para terminal integrado, interface de chat com streaming, e layout com painéis redimensionáveis.

## Motivation

A interface inspirada em Lovable/Replit precisa de componentes especializados para:
1. **Editor de código** - Visualizar e editar código WLanguage/Python
2. **Grafo interativo** - Navegar dependências entre elementos
3. **Terminal** - Acompanhar execuções do Claude Code
4. **Chat** - Interagir com o assistente de conversão
5. **Layout flexível** - Organizar painéis conforme preferência do usuário

## Scope

### In Scope
- Monaco Editor wrapper com syntax highlighting
- Configuração de linguagem WLanguage básica
- React Flow wrapper para grafo de dependências
- Nós customizados por tipo de elemento
- XTerm.js wrapper para terminal
- ChatInterface com mensagens e input
- ResizablePanels usando react-resizable-panels
- Sidebar de navegação
- Header com breadcrumbs

### Out of Scope
- Syntax highlighting WLanguage completo (futuro)
- Terminal com execução real (usa mock nesta fase)
- Integração completa com backend (hooks já prontos)
- Dark mode premium (Fase 5)

## Dependencies

- `frontend-infrastructure` (completed) - Hooks useChat, useTokenUsage
- shadcn/ui configurado
- TanStack Query configurado

## Related Specs

- `editor-components` - Monaco Editor e DiffViewer
- `graph-components` - React Flow e nós customizados
- `terminal-components` - XTerm.js wrapper
- `chat-components` - Interface de chat
- `layout-components` - Painéis e navegação
