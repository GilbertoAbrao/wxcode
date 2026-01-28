# WXCODE CLI Reference

Comandos organizados em ordem topológica (ordem de execução no workflow).

> **Nota:** A partir de v4, a conversão é feita via LLM-driven generation usando Claude Code.
> O frontend (http://localhost:3000) oferece interface visual para todo o workflow.

---

## Fase 1: Setup e Importação

| # | Comando | Função |
|---|---------|--------|
| 1 | `purge` | Remove completamente um projeto e todos os seus dados (MongoDB + Neo4j) |
| 2 | `import` | Importa um projeto WinDev/WebDev para o MongoDB (streaming) |
| 3 | `split-pdf` | Divide PDF de documentação em PDFs individuais por elemento |
| 4 | `init-project` | Gera o starter kit da stack target |

---

## Fase 2: Parsing e Enriquecimento

| # | Comando | Função |
|---|---------|--------|
| 5 | `parse-schema` | Parseia o schema do banco (.xdd) → tables, fields, constraints, connections |
| 6 | `parse-classes` | Parseia classes (.wdc) → methods, properties, inheritance |
| 7 | `parse-procedures` | Parseia procedures (.wdg) → global procedures |
| 8 | `enrich` | Enriquece elementos com controles, eventos, procedures locais, dependências |

---

## Fase 3: Análise de Dependências

| # | Comando | Função |
|---|---------|--------|
| 9 | `analyze` | Analisa dependências (grafo NetworkX, ciclos, ordem topológica) |
| 10 | `sync-neo4j` | Sincroniza grafo de dependências para Neo4j |

---

## Fase 4: Conversão (CLI - Legacy)

| # | Comando | Função |
|---|---------|--------|
| 11 | `themes` | Gerencia temas de skills para conversão LLM (list, show) |
| 12 | `convert` | Converte elementos para stack target (schema→domain→service→route→template) |

> **Recomendado:** Use o frontend para conversão com Claude Code interativo.

---

## Comandos de Análise Neo4j

Podem ser executados a qualquer momento após `sync-neo4j`.

| Comando | Função |
|---------|--------|
| `impact` | Analisa impacto de mudanças em um elemento |
| `path` | Encontra caminhos entre dois elementos |
| `hubs` | Encontra nós críticos com muitas conexões |
| `dead-code` | Encontra código potencialmente não utilizado |

---

## Coleta de Contexto GSD

Usado para coletar contexto completo de elementos antes de conversão.

| Comando | Função |
|---------|--------|
| `gsd-context` | Coleta dados (MongoDB + Neo4j), cria branch git, exporta JSONs estruturados e dispara workflow GSD via Claude Code |

**Workflow completo:**
1. Coleta dados do elemento (MongoDB + Neo4j)
2. Cria branch `gsd/{elemento}+{random8}`
3. Gera arquivos JSON (element, controls, dependencies, related-elements, schema, neo4j-analysis)
4. Cria `CONTEXT.md` otimizado para GSD
5. Invoca Claude Code CLI: `/gsd:new-project CONTEXT.md`

**Exemplo:**
```bash
# Coleta contexto completo
wxcode gsd-context PAGE_Login --project Linkpay_ADM

# Auto-detect projeto
wxcode gsd-context PAGE_Login

# Debug mode (sem criar branch, sem invocar GSD)
wxcode gsd-context PAGE_Login --skip-gsd --no-branch

# Customizar output
wxcode gsd-context PAGE_Login --output /tmp/gsd --depth 3
```

**Requer:** Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)

---

## Comandos Utilitários

| Comando | Função |
|---------|--------|
| `list-orphans` | Lista controles órfãos do projeto |
| `check-duplicates` | Verifica projetos com nomes duplicados |

---

## Pipeline Típico Completo

```bash
# Limpeza (se necessário)
wxcode purge Linkpay_ADM

# Importação
wxcode import ./project-refs/Linkpay_ADM
wxcode split-pdf ./Documentation.pdf --output ./output/pdf_docs --project Linkpay_ADM
wxcode init-project Linkpay_ADM -o ./output/generated

# Parsing
wxcode parse-schema ./project-refs/Linkpay_ADM
wxcode parse-classes ./project-refs/Linkpay_ADM
wxcode parse-procedures ./project-refs/Linkpay_ADM
wxcode enrich ./project-refs/Linkpay_ADM --pdf-docs ./output/pdf_docs

# Análise
wxcode analyze Linkpay_ADM --export-dot ./output/deps.dot
wxcode sync-neo4j Linkpay_ADM

# Conversão completa
wxcode convert Linkpay_ADM -o ./output/generated

# Conversão de elemento específico com tema
wxcode convert Linkpay_ADM -e PAGE_Login -o ./output/generated --theme dashlite
```

---

## Exemplos de Uso

### Importar projeto
```bash
wxcode import ./project-refs/Linkpay_ADM
```

### Converter página específica
```bash
wxcode convert Linkpay_ADM -e PAGE_Login -o ./output/generated --theme dashlite
```

### Converter por camada
```bash
wxcode convert Linkpay_ADM --layer schema -o ./output/generated
wxcode convert Linkpay_ADM --layer domain -o ./output/generated
wxcode convert Linkpay_ADM --layer service -o ./output/generated
wxcode convert Linkpay_ADM --layer route -o ./output/generated
wxcode convert Linkpay_ADM --layer template -o ./output/generated
```

### Análise de impacto
```bash
wxcode impact TABLE:CLIENTE
wxcode impact proc:ValidaCPF --depth 3
wxcode impact PAGE_Login --format json
```

### Encontrar caminhos
```bash
wxcode path PAGE_Login TABLE:USUARIO
```

### Listar temas disponíveis
```bash
wxcode themes list
wxcode themes show dashlite
```

---

## Frontend (Recomendado)

O frontend oferece interface visual completa para o workflow de conversão:

```bash
# Iniciar backend + frontend
./start-dev.sh

# Acessar
http://localhost:3000
```

### Funcionalidades do Frontend

| Feature | Descrição |
|---------|-----------|
| Dashboard | Lista Knowledge Bases importadas |
| Workspace | Visualiza elementos, código, grafo |
| Output Projects | Cria projetos de conversão com stack selection |
| Milestones | Converte elementos individuais |
| Terminal Interativo | Comunicação bidirecional com Claude Code |
| File Tree | Visualização em tempo real de arquivos gerados |

### Workflow via Frontend

1. **Importar KB** - Upload de projeto WinDev/WebDev
2. **Criar Output Project** - Selecionar stack target (15 opções)
3. **Criar Milestone** - Selecionar elemento para conversão
4. **Terminal Interativo** - Responder perguntas do Claude Code
5. **Visualizar Resultado** - File tree com arquivos gerados

---

## MCP Server

O MCP Server expõe a Knowledge Base para Claude Code:

```bash
# Listar tools disponíveis
wxcode mcp-tools

# Testar MCP Server
python -m wxcode.mcp.server
```

### Tools Disponíveis (19 total)

**KB Read (9 tools):**
- `get_element`, `list_elements`, `search_elements`
- `get_controls`, `get_procedures`, `get_schema`
- `get_dependencies`, `get_project_stats`, `list_projects`

**Neo4j Analysis (6 tools):**
- `analyze_impact`, `find_paths`, `find_hubs`
- `find_dead_code`, `detect_cycles`, `get_subgraph`

**Conversion (4 tools):**
- `get_next_element`, `get_conversion_stats`
- `mark_converted`, `get_conversion_context`
