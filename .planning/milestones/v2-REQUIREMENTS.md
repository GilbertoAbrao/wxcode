# Requirements Archive: v2 MCP Server KB Integration

**Archived:** 2026-01-22
**Status:** SHIPPED

This is the archived requirements specification for v2.
For current requirements, see `.planning/REQUIREMENTS.md` (created for next milestone).

---

# Requirements: MCP Server KB Integration

**Defined:** 2026-01-21
**Core Value:** Desenvolvedores devem conseguir migrar sistemas legados WinDev para stacks modernas de forma sistematica.

## v2 Requirements

Requirements for MCP Server KB Integration milestone. Each maps to roadmap phases.

### Infrastructure

- [x] **INFRA-01**: MCP Server inicializa com FastMCP e conecta ao MongoDB
- [x] **INFRA-02**: MCP Server conecta ao Neo4j com fallback graceful
- [x] **INFRA-03**: Configuracao via .mcp.json para Claude Code
- [x] **INFRA-04**: Logging estruturado para stderr (nao stdout)

### Core Retrieval Tools

- [x] **CORE-01**: Tool `get_element` retorna definicao completa (codigo, AST, dependencias, status)
- [x] **CORE-02**: Tool `list_elements` lista elementos com filtros (projeto, tipo, layer, status)
- [x] **CORE-03**: Tool `search_code` busca padroes regex em raw_content e AST

### UI/Control Tools

- [x] **UI-01**: Tool `get_controls` retorna hierarquia de controles com propriedades e eventos
- [x] **UI-02**: Tool `get_data_bindings` extrai mapeamento controle -> campo de tabela

### Procedure Tools

- [x] **PROC-01**: Tool `get_procedures` lista procedures de um elemento com codigo
- [x] **PROC-02**: Tool `get_procedure` retorna procedure especifica por nome

### Schema Tools

- [x] **SCHEMA-01**: Tool `get_schema` retorna schema completo (tabelas, colunas, conexoes)
- [x] **SCHEMA-02**: Tool `get_table` retorna tabela especifica com detalhes

### Graph Analysis Tools

- [x] **GRAPH-01**: Tool `get_dependencies` retorna dependencias diretas (uses/used_by)
- [x] **GRAPH-02**: Tool `get_impact` analisa impacto de mudanca em elemento
- [x] **GRAPH-03**: Tool `get_path` encontra caminho entre dois elementos
- [x] **GRAPH-04**: Tool `find_hubs` identifica nos criticos com muitas conexoes
- [x] **GRAPH-05**: Tool `find_dead_code` detecta procedures/classes nao utilizadas
- [x] **GRAPH-06**: Tool `find_cycles` detecta dependencias circulares

### Conversion Workflow Tools

- [x] **CONV-01**: Tool `get_conversion_candidates` retorna elementos prontos para converter
- [x] **CONV-02**: Tool `get_topological_order` retorna ordem de conversao recomendada
- [x] **CONV-03**: Tool `mark_converted` atualiza status de conversao (escrita)
- [x] **CONV-04**: Tool `get_conversion_stats` retorna estatisticas de progresso

### GSD Integration

- [x] **GSD-01**: Template customizado para milestone de conversao WinDev
- [x] **GSD-02**: Template de phase que consulta KB automaticamente
- [x] **GSD-03**: Documentacao de integracao GSD + MCP

## Traceability

Which phases cover which requirements.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 4 | Complete |
| INFRA-02 | Phase 4 | Complete |
| INFRA-03 | Phase 4 | Complete |
| INFRA-04 | Phase 4 | Complete |
| CORE-01 | Phase 5 | Complete |
| CORE-02 | Phase 5 | Complete |
| CORE-03 | Phase 5 | Complete |
| UI-01 | Phase 5 | Complete |
| UI-02 | Phase 5 | Complete |
| PROC-01 | Phase 5 | Complete |
| PROC-02 | Phase 5 | Complete |
| SCHEMA-01 | Phase 5 | Complete |
| SCHEMA-02 | Phase 5 | Complete |
| GRAPH-01 | Phase 6 | Complete |
| GRAPH-02 | Phase 6 | Complete |
| GRAPH-03 | Phase 6 | Complete |
| GRAPH-04 | Phase 6 | Complete |
| GRAPH-05 | Phase 6 | Complete |
| GRAPH-06 | Phase 6 | Complete |
| CONV-01 | Phase 7 | Complete |
| CONV-02 | Phase 7 | Complete |
| CONV-03 | Phase 7 | Complete |
| CONV-04 | Phase 7 | Complete |
| GSD-01 | Phase 7 | Complete |
| GSD-02 | Phase 7 | Complete |
| GSD-03 | Phase 7 | Complete |

**Coverage:**
- v2 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0

---

## Milestone Summary

**Shipped:** 26 of 26 v2 requirements
**Adjusted:** None
**Dropped:** None

---
*Archived: 2026-01-22 as part of v2 milestone completion*
