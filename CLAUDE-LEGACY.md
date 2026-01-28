<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

## IMPORTANTE: Use Skills OpenSpec, NÃO o CLI

**SEMPRE use as skills disponíveis ao invés de executar comandos `openspec` diretamente no terminal:**

| Operação | Skill (USE ISTO) | CLI (NÃO USE) |
|----------|------------------|---------------|
| Criar proposta | `/openspec:proposal` | ~~`openspec` CLI~~ |
| Implementar change | `/openspec:apply` | ~~comandos manuais~~ |
| Arquivar change | `/openspec:archive` | ~~`openspec archive`~~ |

As skills encapsulam todo o workflow correto e garantem consistência. O CLI só deve ser usado para comandos informativos como `openspec list` ou `openspec validate`.

# WXCODE - Conversor Universal WinDev/WebDev/WinDev Mobile

## Visão Geral

O **wxcode** é uma ferramenta de conversão que transforma projetos desenvolvidos na plataforma PC Soft (WinDev, WebDev, WinDev Mobile) para stacks modernas. A stack padrão de conversão é **FastAPI + Jinja2**, escolhida pela curva de aprendizado suave para desenvolvedores WinDev.

O próprio wxcode é desenvolvido em **FastAPI + Jinja2**.

## Stack Tecnológica

- **Backend**: FastAPI (Python 3.11+)
- **Templates**: Jinja2
- **Banco de Dados**: MongoDB (via Motor/Beanie para async)
- **CLI**: Typer
- **LLM**: Claude (Anthropic) para conversão inteligente

## Arquitetura do Pipeline

```
FASE 1: EXTRAÇÃO & ANÁLISE
┌─────────┐    ┌──────────┐    ┌─────────────┐    ┌────────────┐
│ Parser  │───▶│ AST/IR   │───▶│ Dependency  │───▶│  MongoDB   │
│ WinDev  │    │ Generator│    │   Graph     │    │  Storage   │
└─────────┘    └──────────┘    └─────────────┘    └────────────┘

FASE 2: ANÁLISE SEMÂNTICA
┌─────────────┐    ┌──────────────┐    ┌───────────────────────┐
│ Pattern     │───▶│ Business     │───▶│ Architecture          │
│ Recognition │    │ Rules Extract│    │ Blueprint (target)    │
└─────────────┘    └──────────────┘    └───────────────────────┘

FASE 3: CONVERSÃO EM CAMADAS (ordem topológica)
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌──────────┐
│ Schema │──▶│ Domain │──▶│Business│──▶│  API   │──▶│   UI     │
│ (DB)   │   │Entities│   │ Logic  │   │ Layer  │   │ Layer    │
└────────┘   └────────┘   └────────┘   └────────┘   └──────────┘

FASE 4: VALIDAÇÃO & REFINAMENTO
┌─────────────┐    ┌──────────────┐    ┌───────────────────────┐
│ Test Gen    │───▶│ Equivalence  │───▶│ Human Review          │
│ (auto)      │    │ Validation   │    │ & Adjustments         │
└─────────────┘    └──────────────┘    └───────────────────────┘
```

## Ordem de Conversão em Camadas

A conversão DEVE seguir ordem topológica para respeitar dependências:

1. **Schema/Modelo de Dados** (Análise HyperFile .wdd → SQLAlchemy/Pydantic)
2. **Domain Entities** (Classes .wdc → Python classes)
3. **Business Logic** (Procedures .wdg → Services/Use Cases)
4. **API Layer** (REST endpoints .wdrest → FastAPI routes)
5. **UI Layer** (Pages .wwh → Jinja2 templates)

## Schema MongoDB

### Elemento Base
```javascript
{
  _id: ObjectId,
  projectId: ObjectId,

  // Identificação
  sourceType: "page" | "procedure" | "class" | "query" | "report",
  sourceName: "PAGE_Login",
  sourceFile: "PAGE_Login.wwh",
  windevType: 65538,

  // Conteúdo
  rawContent: "...",
  chunks: [
    { index: 0, content: "...", tokens: 3500 },
    { index: 1, content: "...", tokens: 3200, overlapStart: 200 }
  ],

  // AST/IR
  ast: {
    procedures: [...],
    variables: [...],
    controls: [...],
    events: [...],
    queries: [...]
  },

  // Grafo de Dependências
  dependencies: {
    uses: ["ServerProcedures", "classUsuario"],
    usedBy: ["PAGE_PRINCIPAL"],
    dataFiles: ["USUARIO", "CLIENTE"],
    externalAPIs: ["APIFitbank"]
  },

  // Metadados de Conversão
  conversion: {
    status: "pending" | "in_progress" | "converted" | "validated",
    targetStack: "fastapi-jinja2",
    targetFiles: [...],
    convertedContent: {...},
    issues: [],
    humanReviewRequired: false
  },

  topologicalOrder: 15,
  layer: "ui"
}
```

### Control (Controles de UI)
```javascript
{
  _id: ObjectId,
  element_id: ObjectId,           // Página/Window/Report pai
  project_id: ObjectId,

  // Tipo (fonte: campo 'type' do .wwh)
  type_code: 8,                   // Código numérico do tipo
  type_definition_id: ObjectId,   // Referência à tabela de tipos

  // Identificação
  name: "EDT_LOGIN",
  full_path: "CELL_NoName1.EDT_LOGIN",

  // Hierarquia
  parent_control_id: ObjectId,    // Controle pai (CELL, ZONE)
  children_ids: [ObjectId],       // Controles filhos
  depth: 1,                       // Nível na hierarquia

  // Dados do PDF
  properties: {
    height: 24,
    width: 200,
    x_position: 100,
    y_position: 50,
    visible: true,
    enabled: true,
    input_type: "Text",
    // ...
  },

  // Dados do .wwh
  events: [
    { type_code: 851994, event_name: "OnClick", code: "...", role: "S" }
  ],
  code_blocks: [...],
  windev_internal_properties: {...},

  // Flags
  is_orphan: false,               // True se existe no .wwh mas não no PDF
  is_container: false,            // True se pode conter outros controles
  has_code: true,

  created_at: Date,
  updated_at: Date
}
```

### ControlTypeDefinition (Tabela Dinâmica de Tipos)
```javascript
{
  _id: ObjectId,
  type_code: 8,                   // Código numérico (único)
  type_name: "Edit",              // Nome definido manualmente
  inferred_name: "Edit",          // Inferido pelo prefixo (EDT_→Edit)
  is_container: false,            // True para CELL, ZONE, TAB, etc.
  first_seen_in: "PAGE_Login",    // Primeiro elemento onde foi encontrado
  occurrences: 150,               // Quantas vezes apareceu
  example_names: ["EDT_LOGIN", "EDT_SENHA", "EDT_EMAIL"],
  created_at: Date,
  updated_at: Date
}
```

## Tipos de Elementos WinDev

| Extensão | Tipo Numérico | Descrição |
|----------|---------------|-----------|
| .wwp | - | Projeto WebDev |
| .wwh | 65538 | Página Web |
| .wwt | 65541 | Template de Página |
| .wwn | 65539 | Browser Procedures (JS) |
| .wdg | 7 | Grupo de Procedures (Server) |
| .wdc | 4 | Classe |
| .WDR | 5 | Query SQL |
| .wde | - | Relatório |
| .wdrest | - | API REST |
| .wdsdl | 22 | Webservice WSDL |
| .wdd | - | Análise (modelo de dados) |

## Mapeamento WLanguage → Python

### Tipos de Dados
| WLanguage | Python |
|-----------|--------|
| string / chaîne | str |
| int / entier | int |
| real / réel | float |
| boolean / booléen | bool |
| date | datetime.date |
| datetime | datetime.datetime |
| buffer | bytes |
| variant | Any |
| array | list |
| associative array | dict |
| structure | dataclass / Pydantic model |
| class | class |

### Estruturas de Controle
| WLanguage | Python |
|-----------|--------|
| IF...THEN...ELSE...END | if...elif...else |
| SWITCH...CASE...END | match...case (3.10+) |
| FOR i = 1 TO n | for i in range(1, n+1) |
| FOR EACH...END | for item in iterable |
| WHILE...END | while |
| LOOP...END | while True: ... break |
| RESULT | return |

### Funções Comuns
| WLanguage | Python |
|-----------|--------|
| Length() | len() |
| Left(s, n) | s[:n] |
| Right(s, n) | s[-n:] |
| Middle(s, start, len) | s[start-1:start-1+len] |
| Val() | int() / float() |
| DateToString() | .strftime() |
| StringToDate() | datetime.strptime() |
| JSONToVariant() | json.loads() |
| VariantToJSON() | json.dumps() |
| HTTPRequest() | httpx / requests |
| HReadFirst/HReadNext | ORM query iteration |
| HAdd | ORM create |
| HModify | ORM update |
| HDelete | ORM delete |
| HExecuteQuery | ORM raw SQL |

## Comandos CLI

```bash
# Importar projeto WinDev (streaming para arquivos grandes)
wxcode import ./Projeto.wwp --batch-size 100

# Dividir PDF de documentação em arquivos individuais por elemento
# Use --project para detectar elementos conhecidos (reduz órfãos em ~82%)
wxcode split-pdf ./Documentation_Projeto.pdf --output ./output/pdf_docs --project NomeProjeto

# Enriquecer elementos com controles, propriedades, procedures locais e dependências
# (detecta nome do projeto automaticamente)
wxcode enrich ./caminho/projeto --pdf-docs ./output/pdf_docs

# Parsear schema do banco de dados (Analysis .xdd)
wxcode parse-schema ./caminho/projeto

# Parsear classes (.wdc)
wxcode parse-classes ./caminho/projeto

# Analisar dependências (constrói grafo, detecta ciclos, ordena topologicamente)
wxcode analyze nome_projeto
wxcode analyze nome_projeto --export-dot ./output/deps.dot  # Exporta para GraphViz
wxcode analyze nome_projeto --no-persist  # Não salva ordem no MongoDB

# Planejar conversão
wxcode plan --project nome_projeto --target fastapi-jinja2

# Converter por camada
wxcode convert --project nome_projeto --layer schema
wxcode convert --project nome_projeto --layer domain
wxcode convert --project nome_projeto --layer business
wxcode convert --project nome_projeto --layer api
wxcode convert --project nome_projeto --layer ui

# Validar conversão
wxcode validate --project nome_projeto --generate-tests

# Exportar projeto convertido
wxcode export --project nome_projeto --output ./projeto-python

# --- Comandos Neo4j (análise avançada de grafos) ---

# Sincronizar grafo de dependências para Neo4j
wxcode sync-neo4j nome_projeto
wxcode sync-neo4j nome_projeto --dry-run  # Preview sem modificar
wxcode sync-neo4j nome_projeto --no-clear  # Não limpa dados antes

# Análise de impacto: o que muda se eu alterar X?
wxcode impact TABLE:CLIENTE
wxcode impact proc:ValidaCPF --depth 3
wxcode impact PAGE_Login --format json

# Encontrar caminhos entre dois elementos
wxcode path PAGE_Login TABLE:USUARIO
wxcode path classCliente proc:ValidaCPF

# Encontrar nós críticos (hubs) com muitas conexões
wxcode hubs --min-connections 10
wxcode hubs -m 5 -p Linkpay_ADM

# Encontrar código potencialmente não utilizado
wxcode dead-code
wxcode dead-code -p Linkpay_ADM
```

## Decisões Arquiteturais

Ver pasta `docs/adr/` para ADRs completos:
- ADR-001: Escolha da stack FastAPI + Jinja2
- ADR-002: MongoDB como banco de dados intermediário
- ADR-003: Pipeline de conversão em camadas
- ADR-004: Uso de AST/IR para conversão inteligente
- ADR-005: Chunking semântico para elementos grandes

## Projeto de Referência

O projeto `project-refs/Linkpay_ADM/` contém um projeto WebDev 26 real usado como referência para desenvolvimento e testes.

## Convenções de Código

- Python 3.11+
- Type hints obrigatórios
- Docstrings em português
- Async/await para I/O (MongoDB, HTTP)
- Pydantic para validação de dados
- pytest para testes

## Estrutura de Diretórios

```
wxcode/
├── CLAUDE.md                    # Este arquivo
├── docs/
│   ├── architecture.md
│   ├── wlanguage-reference.md
│   ├── conversion-rules.md
│   └── adr/
├── skills/
│   ├── wx-parser.md
│   ├── wx-analyzer.md
│   └── wx-to-fastapi.md
├── src/wxcode/
│   ├── main.py                  # FastAPI app
│   ├── cli.py                   # Typer CLI (import, split-pdf, enrich)
│   ├── models/                  # Pydantic/Beanie models
│   │   ├── project.py           # Model Project
│   │   ├── element.py           # Model Element
│   │   ├── control.py           # Model Control (controles UI)
│   │   ├── control_type.py      # Model ControlTypeDefinition
│   │   └── conversion.py        # Model Conversion
│   ├── parser/                  # Parsers WinDev
│   │   ├── wwp_parser.py        # Parser .wwp básico
│   │   ├── line_reader.py       # Leitor async streaming
│   │   ├── project_mapper.py    # Mapper com batches MongoDB
│   │   ├── pdf_doc_splitter.py  # Divisor de PDFs documentação
│   │   ├── wwh_parser.py        # Parser .wwh/.wdw (controles, eventos)
│   │   ├── pdf_element_parser.py # Parser propriedades visuais PDF
│   │   └── element_enricher.py  # Orquestrador enriquecimento
│   ├── analyzer/                # Análise de dependências
│   ├── graph/                   # Integração Neo4j
│   │   ├── neo4j_connection.py  # Conexão com Neo4j
│   │   ├── neo4j_sync.py        # Sincronização MongoDB→Neo4j
│   │   └── impact_analyzer.py   # Análise de impacto e queries
│   ├── converter/               # Conversores por stack
│   ├── templates/               # Jinja2 templates
│   └── api/                     # Rotas FastAPI
├── tests/
│   ├── test_project_mapper.py   # Testes do mapper streaming
│   ├── test_pdf_doc_splitter.py # Testes do PDF splitter
│   ├── test_neo4j_connection.py # Testes Neo4j connection
│   ├── test_neo4j_sync.py       # Testes sync service
│   └── test_impact_analyzer.py  # Testes impact analyzer
└── project-refs/                # Projetos WinDev de referência
```

## Fontes de Dados para Conversão

### Schema do Banco de Dados
O schema do banco vem da **análise** do projeto:
- Referência no `.wwp`: `analysis : .\BD.ana\BD.wda`
- SQL exportado: `<nome>.ana/<nome>.sql` (formato SQL Server)
- Contém CREATE TABLE, índices, constraints

### Classes de Domínio
Arquivos `.wdc` contêm classes WLanguage:
- Definição: `NomeClasse is a Class [, abstract]`
- Herança: `inherits ClassePai`
- Membros com visibilidade: `PUBLIC`, `PROTECTED`, `PRIVATE`
- Métodos: `procedure Nome(): tipo`

## Status do Projeto

### Fase Atual: 4 - CONVERSÃO (Em Progresso)

| Fase | Status | Descrição |
|------|--------|-----------|
| 1. Fundação | ✅ Concluída | Estrutura, models, CLI, FastAPI básico |
| 1.1 Project Mapper | ✅ Implementado | Streaming para arquivos grandes (.wwp/.wdp) |
| 2. Parsing | ✅ Concluída | Parsers para todos tipos de arquivo |
| 2.0 PDF Splitter | ✅ Implementado | Divisão de PDFs de documentação |
| 2.1 Element Enricher | ✅ Implementado | Extração de controles, propriedades, eventos, procedures locais e dependências |
| 2.2 Procedure Parser | ✅ Implementado | Parsing de procedures de arquivos .wdg |
| 2.3 Schema Parser | ✅ Implementado | Parsing de Analysis .xdd (schema do banco) |
| 2.4 Class Parser | ✅ Implementado | Parsing de classes .wdc (herança, membros, métodos) |
| 2.5 Query Parser | ✅ Implementado | Parsing de queries (SQL, parâmetros, tabelas via PDF) |
| 2.6 WLanguage Context | ✅ Implementado | DataBinding, HyperFile Buffer, H* Functions (specs criadas) |
| 3. Análise | ✅ Concluída | Grafo de dependências |
| 3.1 Dependency Graph | ✅ Implementado | Grafo NetworkX com ciclos, ordenação topológica e persistência |
| 4. Conversão | 🔄 Em Progresso | Generators e Orquestrador implementados |
| 4.1-4.5 Generators | ✅ Implementado | Schema, Domain, Service, Route, API, Template generators |
| 4.6 Orquestrador | ✅ Implementado | Coordena generators, filtro seletivo, status tracking |
| 5. Validação | ⏳ Pendente | Testes, verificação de equivalência |
| 6. Exportação | ⏳ Pendente | Geração de projeto completo |
| 7. Interface Web | ⏳ Pendente | Dashboard de gerenciamento |

### Prompts Documentados no ROADMAP.md

| Fase | Prompts Disponíveis |
|------|---------------------|
| 1.1 Project Mapper | ✅ Implementado |
| 2.0 PDF Splitter | ✅ Implementado |
| 2.1 Element Enricher | ✅ Implementado |
| 2.2 Procedure Parser | ✅ Implementado |
| 2.3 Schema Parser | ✅ Implementado |
| 2.4 Class Parser | ✅ Implementado |
| 2.5 Query Parser | ✅ Implementado |
| 2.6 WLanguage Context | ✅ Implementado (specs: data-binding, hyperfile-buffer, hyperfile-functions) |
| 2. Parsing | 2.7 REST, 2.8 Integração |
| 3.1 Dependency Graph | ✅ Implementado |
| 4.1-4.5 Generators | ✅ Implementado (schema, domain, service, route, api, template) |
| 4.6 Orquestrador | ✅ Implementado (GeneratorOrchestrator, ElementFilter) |

### Pipeline de Processamento

A ordem correta de execução é:

```bash
# 1. Importa projeto e mapeia todos os elementos para o MongoDB (streaming)
wxcode import ./Linkpay_ADM.wwp

# 2. Divide o PDF de documentação em PDFs individuais (pages, windows, queries)
#    Use --project para detectar elementos conhecidos (reduz órfãos em ~82%)
wxcode split-pdf ./Documentation_Projeto.pdf --output ./output/pdf_docs --project Linkpay_ADM

# 3. Enriquece elementos:
#    - Pages/Windows: controles, propriedades, eventos, procedures locais
#    - Queries: SQL, parâmetros, tabelas referenciadas
wxcode enrich ./project-refs/Linkpay_ADM --pdf-docs ./output/pdf_docs

# 4. Parseia procedures de arquivos .wdg
wxcode parse-procedures ./project-refs/Linkpay_ADM

# 5. Parseia schema do banco de dados (Analysis .xdd)
wxcode parse-schema ./project-refs/Linkpay_ADM

# 6. Parseia classes (.wdc)
wxcode parse-classes ./project-refs/Linkpay_ADM

# 7. Analisa dependências (grafo, ciclos, ordem topológica)
#    Inclui: tabelas, classes, procedures, pages, queries
wxcode analyze Linkpay_ADM --export-dot ./output/deps.dot

# 8. Conversão para FastAPI + Jinja2
#    Opções:
#    - Projeto completo: wxcode convert Linkpay_ADM -o ./output/generated
#    - Elemento específico: wxcode convert Linkpay_ADM -e PAGE_Login -o ./output/generated
#    - Por camada: wxcode convert Linkpay_ADM --layer route -o ./output/generated
wxcode convert Linkpay_ADM -o ./output/generated
```

### Próximos Passos

- Fase 5: Validação (testes automatizados, verificação de equivalência)
- Fases 6-9: Exportação, REST API Generator, MCP Server Generator, AI Agents

## Quick Start para Nova Sessão

```
Estou desenvolvendo o wxcode, um conversor de projetos WinDev para FastAPI.
Leia o CLAUDE.md e docs/ROADMAP.md para contexto completo.

[COPIE O PROMPT DA TAREFA DESEJADA DO ROADMAP]
```

## Referência Rápida de Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `CLAUDE.md` | Este arquivo - contexto do projeto |
| `docs/ROADMAP.md` | Prompts detalhados para cada fase |
| `docs/adr/` | Decisões arquiteturais |
| `src/wxcode/parser/wwp_parser.py` | Parser do projeto (.wwp) |
| `src/wxcode/parser/line_reader.py` | Leitor async com streaming |
| `src/wxcode/parser/project_mapper.py` | Mapper streaming + MongoDB batches |
| `src/wxcode/parser/pdf_doc_splitter.py` | Divisor de PDFs documentação |
| `src/wxcode/parser/wwh_parser.py` | Parser de arquivos .wwh/.wdw (controles, eventos, procedures locais) |
| `src/wxcode/parser/pdf_element_parser.py` | Parser de propriedades visuais dos PDFs |
| `src/wxcode/parser/element_enricher.py` | Orquestrador de enriquecimento (controles, procedures locais, dependências) |
| `src/wxcode/parser/wdg_parser.py` | Parser de procedures (.wdg) |
| `src/wxcode/parser/xdd_parser.py` | Parser de Analysis (.xdd) - schema do banco |
| `src/wxcode/parser/wdc_parser.py` | Parser de classes (.wdc) - herança, membros, métodos |
| `src/wxcode/parser/query_parser.py` | Parser de queries (SQL, parâmetros, tabelas do PDF) |
| `src/wxcode/parser/query_enricher.py` | Enriquecedor de queries via PDF |
| `src/wxcode/parser/dependency_extractor.py` | Extrator de dependências de código WLanguage |
| `src/wxcode/models/` | Models Pydantic/Beanie |
| `src/wxcode/models/control.py` | Model Control (controles de UI) |
| `src/wxcode/models/control_type.py` | Model ControlTypeDefinition (tabela de tipos) |
| `src/wxcode/models/procedure.py` | Model Procedure (procedures globais e locais) |
| `src/wxcode/models/schema.py` | Model DatabaseSchema (tabelas, colunas, conexões) |
| `src/wxcode/analyzer/` | Módulo de análise de dependências |
| `src/wxcode/analyzer/models.py` | Models do grafo (NodeType, EdgeType, GraphNode, CycleInfo, AnalysisResult) |
| `src/wxcode/analyzer/graph_builder.py` | Constrói grafo NetworkX de dependências |
| `src/wxcode/analyzer/cycle_detector.py` | Detecta ciclos e sugere pontos de quebra |
| `src/wxcode/analyzer/topological_sorter.py` | Ordenação topológica por camadas |
| `src/wxcode/analyzer/dependency_analyzer.py` | Orquestrador de análise (CLI `analyze`) |
| `src/wxcode/generator/` | Módulo de geração de código |
| `src/wxcode/generator/base.py` | BaseGenerator, ElementFilter (filtro seletivo, DBRef queries) |
| `src/wxcode/generator/orchestrator.py` | GeneratorOrchestrator (coordena todos generators) |
| `src/wxcode/generator/schema_generator.py` | Gera models Pydantic/Beanie do schema |
| `src/wxcode/generator/domain_generator.py` | Gera classes de domínio |
| `src/wxcode/generator/service_generator.py` | Gera services de procedures |
| `src/wxcode/generator/route_generator.py` | Gera rotas FastAPI de pages |
| `src/wxcode/generator/api_generator.py` | Gera API routes de REST definitions |
| `src/wxcode/generator/template_generator.py` | Gera templates Jinja2 de pages |
| `src/wxcode/generator/templates/` | Templates Jinja2 para geração |
| `project-refs/Linkpay_ADM/` | Projeto de referência |
| `project-refs/WX_CodeStyle_Prefixes.md` | Prefixos padrão WinDev/WebDev |
