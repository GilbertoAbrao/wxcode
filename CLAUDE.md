# WXCODE

Conversor universal de projetos WinDev/WebDev/WinDev Mobile para stacks modernas.

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| [docs/VISION.md](docs/VISION.md) | Visão estratégica, produtos derivados, princípios |
| [docs/MASTER-PLAN.md](docs/MASTER-PLAN.md) | Fases, dependências, status, próximos passos |
| [TODO.md](TODO.md) | Backlog informal (ideias que ainda não são proposals) |
| [openspec/project.md](openspec/project.md) | Contexto técnico detalhado |
| [docs/architecture.md](docs/architecture.md) | Arquitetura e diagramas |
| [docs/adr/](docs/adr/) | Decisões arquiteturais |

---

## Workflow com OpenSpec

<!-- OPENSPEC:START -->
Sempre abra `@/openspec/AGENTS.md` quando a solicitação:
- Mencionar planejamento ou propostas (proposal, spec, change, plan)
- Introduzir novas capabilities, breaking changes, ou mudanças arquiteturais
- For ambígua e precisar da spec autoritativa antes de codar
<!-- OPENSPEC:END -->

**SEMPRE use as skills, NÃO o CLI:**

| Operação | Skill (USE ISTO) | CLI (NÃO USE) |
|----------|------------------|---------------|
| Criar proposta | `/openspec:proposal` | ~~`openspec` CLI~~ |
| Implementar change | `/openspec:apply` | ~~comandos manuais~~ |
| Arquivar change | `/openspec:archive` | ~~`openspec archive`~~ |

As skills encapsulam todo o workflow correto. O CLI só deve ser usado para comandos informativos como `openspec list` ou `openspec validate`.

### Regra: Tasks otimizadas para Sonnet 4.5

**Ao criar proposals com `/openspec:proposal`**, SEMPRE gerar tasks otimizadas:

- **Máximo 3-5 passos** por task (nunca mais)
- **Um arquivo por task** sempre que possível
- **Acceptance criteria** claros e verificáveis
- **Evitar context switching** entre arquivos/módulos
- **Caminhos explícitos** (`src/wxcode/parser/x.py`, não "no parser")

**Exemplo de task bem estruturada:**
```markdown
## Task 1: Criar dataclass X

**File:** `src/wxcode/models/x.py`

**Steps:**
1. Criar arquivo
2. Criar dataclass com campos A, B, C
3. Adicionar docstring

**Acceptance Criteria:**
- [ ] Arquivo existe
- [ ] Type hints completos
```

**Lembrete pós-proposal:**
> 💡 Antes de `/openspec:apply`, confirme Sonnet 4.5: `/status` ou `/model sonnet`

### Regra: Verificar MASTER-PLAN após OpenSpec changes

**Após `/openspec:archive`**, SEMPRE verificar se o MASTER-PLAN.md precisa ser atualizado:

1. O change completado **muda o status de uma fase**? (ex: última task da Fase 4)
   - Se sim → Atualizar status da fase no MASTER-PLAN.md
2. O change **adiciona nova capability** não prevista?
   - Se sim → Considerar adicionar na seção "Changes Planejados"
3. O change **altera dependências entre fases**?
   - Se sim → Atualizar grafo de dependências

**Não atualizar** o MASTER-PLAN para cada change individual — isso é papel do `openspec list`.

---

## Workflow com Opus (Architect)

Este projeto usa um workflow onde **Opus atua como Architect** e **Sonnet implementa**.

### Papel do Opus (Architect)

| Fase | Responsabilidade |
|------|------------------|
| **Pré-implementação** | Discussão arquitetural, criar proposal, recomendar modelo |
| **Durante** | Alertar interdependências entre changes, responder dúvidas |
| **Pós-implementação** | Code review do diff, resolver conflitos, executar merge |

### Fluxo de trabalho

```
1. Usuário traz problema/feature
2. Opus discute arquitetura e trade-offs
3. Opus cria proposal via /openspec:proposal
4. Opus recomenda: "Sonnet OK" ou "Precisa Opus"
5. Usuário cria worktree com branchlet
6. Sonnet/Opus implementa em paralelo (múltiplas changes simultâneas)
7. Usuário avisa: "branch X pronta"
8. Opus faz code review, resolve conflitos, executa merge
```

### Recomendação de modelo para implementação

| Complexidade | Modelo | Critérios |
|--------------|--------|-----------|
| **Baixa/Média** | Sonnet | Tasks isoladas, um arquivo por task, padrões claros |
| **Alta** | Opus | Múltiplos sistemas interagindo, refactoring extenso, decisões arquiteturais durante implementação |

**Preferência:** Sonnet (menor custo). Opus apenas quando necessário.

### Checklist de Code Review (pré-merge)

- [ ] Código segue padrões do projeto
- [ ] Tasks da proposal foram implementadas
- [ ] Testes incluídos (quando aplicável)
- [ ] Sem regressões óbvias
- [ ] Sem código comentado/debug deixado
- [ ] Type hints presentes

### Alerta de interdependências

Ao criar proposals, Opus DEVE verificar:
1. A nova change depende de outra em andamento?
2. Outra change em andamento será afetada?
3. Há conflitos de escopo entre changes?

Se houver interdependência → alertar usuário antes de prosseguir.

---

## Estado Atual

```bash
# Ver fases e dependências
cat docs/MASTER-PLAN.md

# Ver changes em andamento
openspec list

# Ver specs existentes
ls openspec/specs/
```

**Fase atual:** 4 - Conversão (generators implementados, refinamentos em andamento)

---

## Stack Tecnológica

- **Backend**: FastAPI (Python 3.11+)
- **Templates**: Jinja2
- **Database**: MongoDB (Motor/Beanie async)
- **Graph DB**: Neo4j (análise de dependências)
- **CLI**: Typer
- **LLM**: Claude (conversão inteligente)

---

## Comandos CLI

### Pipeline Principal

```bash
# 1. Importa projeto e mapeia todos os elementos para o MongoDB (streaming)
#    IMPORTANTE: Popula automaticamente o campo raw_content de todos os elementos
wxcode import ./Linkpay_ADM.wwp

# 2. Divide o PDF de documentação em PDFs individuais
#    Use --project para detectar elementos conhecidos (reduz órfãos em ~82%)
wxcode split-pdf ./Documentation_Projeto.pdf --output ./output/pdf_docs --project Linkpay_ADM

# 3. Enriquece elementos (controles, propriedades, eventos, procedures locais, dependências)
#    NOTA: O raw_content já foi populado pelo import. O enrich adiciona parsing de AST,
#    controles, eventos e documentação PDF
wxcode enrich ./project-refs/Linkpay_ADM --pdf-docs ./output/pdf_docs

# 4. Parseia procedures de arquivos .wdg
wxcode parse-procedures ./project-refs/Linkpay_ADM

# 5. Parseia schema do banco de dados (Analysis .xdd)
wxcode parse-schema ./project-refs/Linkpay_ADM

# 6. Parseia classes (.wdc)
wxcode parse-classes ./project-refs/Linkpay_ADM

# 7. Analisa dependências (grafo, ciclos, ordem topológica)
wxcode analyze Linkpay_ADM --export-dot ./output/deps.dot

# 8. Conversão para FastAPI + Jinja2
wxcode convert Linkpay_ADM -o ./output/generated
wxcode convert Linkpay_ADM -e PAGE_Login -o ./output/generated  # Elemento específico
wxcode convert Linkpay_ADM --layer route -o ./output/generated  # Por camada
```

### Comandos Neo4j

```bash
# Sincronizar grafo de dependências para Neo4j
wxcode sync-neo4j nome_projeto
wxcode sync-neo4j nome_projeto --dry-run
wxcode sync-neo4j nome_projeto --no-clear

# Análise de impacto: o que muda se eu alterar X?
wxcode impact TABLE:CLIENTE
wxcode impact proc:ValidaCPF --depth 3
wxcode impact PAGE_Login --format json

# Encontrar caminhos entre dois elementos
wxcode path PAGE_Login TABLE:USUARIO

# Encontrar nós críticos (hubs) com muitas conexões
wxcode hubs --min-connections 10

# Encontrar código potencialmente não utilizado
wxcode dead-code
```

### Comando GSD (Get Stuff Done)

```bash
# Coleta contexto completo de elemento e dispara workflow GSD
wxcode gsd-context PAGE_Login --project Linkpay_ADM
wxcode gsd-context PAGE_Login  # Auto-detect projeto

# Modo debug (sem criar branch, sem invocar GSD)
wxcode gsd-context PAGE_Login --skip-gsd --no-branch

# Customizar output e profundidade Neo4j
wxcode gsd-context PAGE_Login --output /tmp/gsd --depth 3
```

**Workflow:**
1. Coleta dados completos (MongoDB + Neo4j)
2. Cria branch git `gsd/{elemento}+{random8}`
3. Cria pasta `./output/gsd-context/{elemento}/`
4. Grava arquivos JSON estruturados:
   - `element.json` - Elemento completo (AST, raw_content, dependencies)
   - `controls.json` - Hierarquia de controles (eventos, propriedades, bindings)
   - `dependencies.json` - Grafo de dependências (Neo4j + MongoDB)
   - `related-elements.json` - Elementos relacionados diretos (até 50)
   - `schema.json` - Tabelas vinculadas (se houver)
   - `neo4j-analysis.json` - Análise de impacto (se Neo4j disponível)
5. Cria `CONTEXT.md` - Master file otimizado para GSD
6. Invoca Claude Code CLI: `/gsd:new-project CONTEXT.md`

**Requer:** Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)

**Fallback graceful:** Se Neo4j indisponível, usa apenas MongoDB.

---

## Ordem de Conversão (Topológica)

A conversão DEVE seguir ordem topológica para respeitar dependências:

```
1. Schema   (.wdd → Pydantic)     → spec: schema-generator
2. Domain   (.wdc → classes)      → spec: domain-generator
3. Service  (.wdg → services)     → spec: service-generator
4. Route    (.wwh → FastAPI)      → spec: route-generator
5. Template (.wwh → Jinja2)       → spec: template-generator
```

---

## Schema MongoDB

### Element
```javascript
{
  _id: ObjectId,
  projectId: ObjectId,
  sourceType: "page" | "procedure" | "class" | "query" | "report",
  sourceName: "PAGE_Login",
  sourceFile: "PAGE_Login.wwh",
  windevType: 65538,
  rawContent: "...",
  chunks: [
    { index: 0, content: "...", tokens: 3500 },
    { index: 1, content: "...", tokens: 3200, overlapStart: 200 }
  ],
  ast: {
    procedures: [...],
    variables: [...],
    controls: [...],
    events: [...],
    queries: [...]
  },
  dependencies: {
    uses: ["ServerProcedures", "classUsuario"],
    usedBy: ["PAGE_PRINCIPAL"],
    dataFiles: ["USUARIO", "CLIENTE"],
    externalAPIs: ["APIFitbank"]
  },
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

### Control
```javascript
{
  _id: ObjectId,
  element_id: ObjectId,
  project_id: ObjectId,
  type_code: 8,
  type_definition_id: ObjectId,
  name: "EDT_LOGIN",
  full_path: "CELL_NoName1.EDT_LOGIN",
  parent_control_id: ObjectId,
  children_ids: [ObjectId],
  depth: 1,
  properties: {
    height: 24,
    width: 200,
    x_position: 100,
    y_position: 50,
    visible: true,
    enabled: true,
    input_type: "Text"
  },
  events: [
    { type_code: 851994, event_name: "OnClick", code: "...", role: "S" }
  ],
  code_blocks: [...],
  is_orphan: false,
  is_container: false,
  has_code: true
}
```

### ControlTypeDefinition
```javascript
{
  _id: ObjectId,
  type_code: 8,
  type_name: "Edit",
  inferred_name: "Edit",
  is_container: false,
  first_seen_in: "PAGE_Login",
  occurrences: 150,
  example_names: ["EDT_LOGIN", "EDT_SENHA", "EDT_EMAIL"]
}
```

---

## Tipos de Elementos WinDev

| Extensão | Tipo Numérico | Descrição | Camada |
|----------|---------------|-----------|--------|
| .wwp | - | Projeto WebDev | - |
| .wwh | 65538 | Página Web | UI |
| .wwt | 65541 | Template de Página | UI |
| .wwn | 65539 | Browser Procedures (JS) | UI |
| .wdg | 7 | Grupo de Procedures (Server) | Business |
| .wdc | 4 | Classe | Domain |
| .WDR | 5 | Query SQL | Schema |
| .wde | - | Relatório | UI |
| .wdrest | - | API REST | API |
| .wdsdl | 22 | Webservice WSDL | API |
| .wdd/.wda | - | Análise (schema) | Schema |

---

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
| structure | dataclass / Pydantic |
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

---

## Estrutura de Diretórios

```
wxcode/
├── CLAUDE.md                    # Este arquivo
├── docs/
│   ├── VISION.md                # Visão estratégica
│   ├── MASTER-PLAN.md           # Plano diretor
│   ├── architecture.md
│   ├── wlanguage-reference.md
│   └── adr/
├── openspec/
│   ├── project.md               # Contexto técnico
│   ├── AGENTS.md                # Instruções para AI
│   ├── specs/                   # Source of truth
│   ├── changes/                 # Em andamento
│   └── archive/                 # Histórico
├── src/wxcode/
│   ├── main.py                  # FastAPI app
│   ├── cli.py                   # Typer CLI
│   ├── models/                  # Pydantic/Beanie
│   ├── parser/                  # Parsers WinDev
│   ├── analyzer/                # Grafo de dependências
│   ├── graph/                   # Integração Neo4j
│   ├── generator/               # Geradores de código
│   └── api/                     # Rotas FastAPI
├── tests/
└── project-refs/
    └── Linkpay_ADM/             # Projeto de referência
```

---

## Referência de Arquivos

### Parsers
| Arquivo | Função |
|---------|--------|
| `parser/project_mapper.py` | Streaming + MongoDB batches |
| `parser/wwh_parser.py` | Controles, eventos, procedures locais |
| `parser/wdg_parser.py` | Procedures globais |
| `parser/xdd_parser.py` | Schema do banco |
| `parser/wdc_parser.py` | Classes |
| `parser/query_parser.py` | Queries SQL |
| `parser/pdf_doc_splitter.py` | Divisor de PDFs |
| `parser/element_enricher.py` | Orquestrador de enriquecimento |
| `parser/dependency_extractor.py` | Extrator de dependências |

### Analyzers
| Arquivo | Função |
|---------|--------|
| `analyzer/graph_builder.py` | Constrói grafo NetworkX |
| `analyzer/cycle_detector.py` | Detecta ciclos |
| `analyzer/topological_sorter.py` | Ordena por camadas |
| `analyzer/dependency_analyzer.py` | Orquestrador (CLI `analyze`) |
| `graph/neo4j_sync.py` | Sync MongoDB→Neo4j |
| `graph/impact_analyzer.py` | Análise de impacto |

### Generators
| Arquivo | Função |
|---------|--------|
| `generator/orchestrator.py` | Coordena todos generators |
| `generator/base.py` | BaseGenerator, ElementFilter |
| `generator/schema_generator.py` | Pydantic models |
| `generator/domain_generator.py` | Classes de domínio |
| `generator/service_generator.py` | Services de procedures |
| `generator/route_generator.py` | Rotas FastAPI |
| `generator/api_generator.py` | API routes REST |
| `generator/template_generator.py` | Templates Jinja2 |

### Models
| Arquivo | Função |
|---------|--------|
| `models/project.py` | Model Project |
| `models/element.py` | Model Element |
| `models/control.py` | Model Control |
| `models/control_type.py` | Model ControlTypeDefinition |
| `models/procedure.py` | Model Procedure |
| `models/schema.py` | Model DatabaseSchema |
| `models/conversion.py` | Model Conversion |

---

## Convenções

- **Python**: 3.11+, type hints obrigatórios
- **Docstrings**: Em português
- **I/O**: Async/await (MongoDB, HTTP)
- **Validação**: Pydantic
- **Testes**: pytest
- **Batch size**: 100 documentos (MongoDB)

---

## ADRs

Ver pasta `docs/adr/`:
- ADR-001: Escolha da stack FastAPI + Jinja2
- ADR-002: MongoDB como banco intermediário
- ADR-003: Pipeline de conversão em camadas
- ADR-004: Uso de AST/IR para conversão inteligente
- ADR-005: Chunking semântico para elementos grandes

---

## Quick Start para Claude Code

### Iniciar nova sessão
```
Leia CLAUDE.md para contexto do projeto wxcode.
```

### Criar nova feature
```
Leia CLAUDE.md e docs/MASTER-PLAN.md para contexto.
Preciso implementar [descrição da feature].
Use /openspec:proposal para criar a proposta.
```

### Mudar arquitetura/pipeline
```
Leia CLAUDE.md, docs/adr/003-conversion-pipeline.md e openspec/project.md.
Preciso alterar a pipeline de conversão para [descrição].
Use /openspec:proposal para criar a proposta.
```

### Continuar trabalho em andamento
```
Leia CLAUDE.md para contexto.
Execute: openspec list
Depois leia o change ativo e continue a implementação.
```

### Corrigir bug em componente específico
```
Leia CLAUDE.md e openspec/specs/[componente]/spec.md.
Preciso corrigir [descrição do bug].
```

### Ver estado do projeto
```
Leia docs/MASTER-PLAN.md para ver fases e status.
Execute: openspec list
```

### Adicionar ideia ao backlog
```
Adicione ao TODO.md na seção apropriada:
- [ ] [descrição da ideia]
```
