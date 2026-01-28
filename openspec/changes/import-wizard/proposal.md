# Import Wizard

## Summary

Wizard de importação de projetos no frontend que guia o usuário pelas etapas de construção da Knowledge Database e Agent Coder especializado.

## Motivation

Atualmente, a importação de projetos WinDev/WebDev requer execução manual de múltiplos comandos CLI em sequência (`import`, `enrich`, `parse-*`, `analyze`, `sync-neo4j`). O usuário precisa entender a ordem correta e monitorar cada etapa individualmente.

O Import Wizard transforma essa experiência em um fluxo guiado que:
1. **Agrega valor visível** - Mostra o "conhecimento" sendo construído
2. **Projeta expertise** - Comunica a construção de uma Knowledge Database
3. **Reduz atrito** - Interface visual substitui comandos CLI
4. **Mostra progresso** - Logs em tempo real e resumo por etapa

## User Stories

1. Como usuário, quero fazer upload de um projeto WinDev e ver cada etapa do processamento
2. Como usuário, quero acompanhar logs em tempo real durante o import
3. Como usuário, quero ver um resumo do "conhecimento" extraído ao final
4. Como usuário, quero poder pular etapas opcionais (PDF docs, Neo4j)

## Scope

### In Scope

- Backend: API endpoints para execução de cada etapa com streaming
- Backend: WebSocket para logs e progresso em tempo real
- Frontend: Wizard multi-step com visualização de progresso
- Frontend: Área de logs em tempo real (estilo terminal)
- Frontend: Resumo final do projeto importado
- Integração com comandos CLI existentes (`import`, `enrich`, `parse-*`, `analyze`, `sync-neo4j`)

### Out of Scope

- Upload de arquivos via browser (usa path local)
- Edição de configurações avançadas de parsing
- Rollback/undo de importação
- Múltiplos projetos simultâneos

## Steps

| # | Step | CLI Equivalente | Obrigatório |
|---|------|-----------------|-------------|
| 1 | Project Selection | - | ✅ |
| 2 | Import (Element Mapping) | `wxcode import` | ✅ |
| 3 | Enrich (Controls/Events) | `wxcode enrich` | ✅ |
| 4 | Parse (Procedures/Classes/Schema) | `wxcode parse-*` | ✅ |
| 5 | Analyze (Dependencies) | `wxcode analyze` | ✅ |
| 6 | Sync Neo4j | `wxcode sync-neo4j` | ❌ |

## Technical Approach

### Backend

1. **Import Session Model** - Armazena estado do wizard por sessão
2. **Step Executor** - Executa comandos CLI como subprocessos
3. **WebSocket Handler** - Stream de logs e progresso
4. **Step Results** - Métricas e resumo de cada etapa

### Frontend

1. **Stepper Component** - Navegação visual entre etapas
2. **Log Viewer** - Terminal-like para logs em tempo real
3. **Progress Indicators** - Barras de progresso e contadores
4. **Summary Cards** - Resumo do conhecimento extraído

## Dependencies

- `frontend-infrastructure` - WebSocket já implementado
- `frontend-components` - Componentes base já existem
- CLI commands já implementados (`import`, `enrich`, `parse-*`, `analyze`, `sync-neo4j`)

## Acceptance Criteria

- [ ] Usuário pode iniciar wizard e selecionar projeto
- [ ] Cada etapa executa o comando CLI correspondente
- [ ] Logs aparecem em tempo real via WebSocket
- [ ] Progresso é mostrado visualmente
- [ ] Resumo final mostra estatísticas do projeto
- [ ] Etapas opcionais podem ser puladas
