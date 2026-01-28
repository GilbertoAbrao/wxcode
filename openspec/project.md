# Project Context

## Purpose
O **wxcode** é uma ferramenta de conversão que transforma projetos desenvolvidos na plataforma PC Soft (WinDev, WebDev, WinDev Mobile) para stacks modernas. A stack padrão de conversão é **FastAPI + Jinja2**, escolhida pela curva de aprendizado suave para desenvolvedores WinDev.

O próprio wxcode é desenvolvido em **FastAPI + Jinja2**.

**Objetivos principais:**
- Extrair e parsear projetos WinDev (.wwp, .wwh, .wdg, .wdc, etc.)
- Armazenar estrutura intermediária no MongoDB para análise
- Converter código WLanguage para Python seguindo ordem topológica de dependências
- Gerar projeto FastAPI + Jinja2 funcional

## Tech Stack
- **Runtime**: Python 3.11+
- **Backend Framework**: FastAPI
- **Templates**: Jinja2
- **Database**: MongoDB (via Motor/Beanie para async)
- **CLI**: Typer
- **PDF Processing**: pdfplumber (extração de propriedades visuais)
- **LLM**: Claude (Anthropic) para conversão inteligente
- **Testing**: pytest
- **Async I/O**: aiofiles (streaming de arquivos grandes)

## Project Status

### Fase Atual: 2 - PARSING

| Fase | Status | Descrição |
|------|--------|-----------|
| 1. Fundação | ✅ Concluída | Estrutura, models, CLI, FastAPI básico |
| 1.1 Project Mapper | ✅ Implementado | Streaming para arquivos grandes (.wwp/.wdp) |
| 2. Parsing | 🔄 Em andamento | Parsers para todos tipos de arquivo |
| 2.0 PDF Splitter | ✅ Implementado | Divisão de PDFs de documentação |
| 2.1 Element Enricher | ✅ Implementado | Extração de controles, propriedades e eventos |
| 2.2-2.7 Parsers | 📝 Documentados | Procedures, Classes, Queries, REST |
| 3. Análise | 📝 Documentada | Grafo de dependências |
| 4. Conversão | 📝 Documentada | Schema, Domain, Business, API, UI |
| 5-8 | ⏳ Pendentes | Validação, Exportação, Interface, Refinamentos |

## Architecture

### Pipeline de Conversão
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

### Ordem de Conversão em Camadas
A conversão DEVE seguir ordem topológica para respeitar dependências:

1. **Schema/Modelo de Dados** (.wdd/.wda → Pydantic/SQLAlchemy)
2. **Domain Entities** (.wdc classes → Python classes)
3. **Business Logic** (.wdg procedures → Services/Use Cases)
4. **API Layer** (.wdrest → FastAPI routes)
5. **UI Layer** (.wwh pages → Jinja2 templates)

### Pipeline de Processamento CLI
```bash
# 1. Importa projeto e mapeia todos os elementos para o MongoDB (streaming)
wxcode import ./Linkpay_ADM.wwp

# 2. Divide o PDF de documentação em PDFs individuais
wxcode split-pdf ./Documentation_Projeto.pdf --output ./output/pdf_docs

# 3. Enriquece elementos com controles, propriedades e eventos
wxcode enrich ./project-refs/Linkpay_ADM --pdf-docs ./output/pdf_docs

# 4. Parsers específicos processam cada tipo de elemento
# 5. Análise de dependências (3.x)
# 6. Conversão por camadas (4.x)
```

## Project Conventions

### Code Style
- Type hints obrigatórios em todas as funções
- Docstrings em português (projeto brasileiro)
- Async/await para todas as operações de I/O (MongoDB, HTTP, arquivos)
- Pydantic para validação de dados e models
- Formatação com Black (implícito)
- Imports organizados: stdlib, third-party, local

### Naming Conventions
- **Arquivos**: snake_case (`element_enricher.py`)
- **Classes**: PascalCase (`ElementEnricher`)
- **Funções/métodos**: snake_case (`parse_controls()`)
- **Constantes**: UPPER_SNAKE_CASE (`PREFIX_TO_TYPE_NAME`)
- **Models Beanie**: PascalCase, singular (`Element`, `Control`)

### Architecture Patterns
- **Pipeline de conversão em camadas**: Schema → Domain → Business → API → UI
- **Streaming para arquivos grandes**: Evitar carregar arquivos completos em memória
- **Batch processing**: Operações MongoDB em lotes (padrão: 100 documentos)
- **Parsers especializados**: Um parser por tipo de arquivo WinDev
- **Enrichment pattern**: Enriquecer elementos com dados de múltiplas fontes (wwh + PDF)

### Directory Structure
```
wxcode/
├── CLAUDE.md                    # Contexto do projeto para Claude
├── docs/
│   ├── ROADMAP.md               # Prompts detalhados para cada fase
│   ├── architecture.md
│   ├── wlanguage-reference.md
│   └── adr/                     # Decisões arquiteturais
├── openspec/                    # OpenSpec specifications
│   ├── project.md               # Este arquivo
│   ├── specs/                   # Specs atuais
│   └── changes/                 # Proposals em andamento
├── src/wxcode/
│   ├── main.py                  # FastAPI app
│   ├── cli.py                   # Typer CLI (import, split-pdf, enrich)
│   ├── models/                  # Pydantic/Beanie models
│   │   ├── project.py           # Model Project
│   │   ├── element.py           # Model Element
│   │   ├── control.py           # Model Control (controles UI)
│   │   └── control_type.py      # Model ControlTypeDefinition
│   ├── parser/                  # Parsers WinDev
│   │   ├── wwp_parser.py        # Parser .wwp básico
│   │   ├── line_reader.py       # Leitor async streaming
│   │   ├── project_mapper.py    # Mapper com batches MongoDB
│   │   ├── pdf_doc_splitter.py  # Divisor de PDFs documentação
│   │   ├── wwh_parser.py        # Parser .wwh/.wdw (controles, eventos)
│   │   ├── pdf_element_parser.py # Parser propriedades visuais PDF
│   │   └── element_enricher.py  # Orquestrador enriquecimento
│   ├── analyzer/                # Análise de dependências
│   ├── converter/               # Conversores por stack
│   ├── templates/               # Jinja2 templates
│   └── api/                     # Rotas FastAPI
├── tests/
│   ├── test_project_mapper.py
│   └── test_pdf_doc_splitter.py
└── project-refs/                # Projetos WinDev de referência
    └── Linkpay_ADM/             # Projeto WebDev 26 real
```

### Testing Strategy
- pytest para todos os testes
- Fixtures para conexão MongoDB de teste
- Mocks para operações de arquivo
- Testes de integração com projeto de referência (`project-refs/Linkpay_ADM/`)

### Git Workflow
- Branch por feature: `feature/nome-descritivo`
- Commits em inglês, mensagens descritivas
- Co-authored by Claude quando aplicável
- Merge para `main` após revisão

### Architectural Decision Records (ADRs)
- **ADR-001**: Escolha da stack FastAPI + Jinja2
- **ADR-002**: MongoDB como banco de dados intermediário
- **ADR-003**: Pipeline de conversão em camadas
- **ADR-004**: Uso de AST/IR para conversão inteligente
- **ADR-005**: Chunking semântico para elementos grandes

## Domain Context

### WinDev/WebDev Platform
- **PC Soft**: Empresa francesa que desenvolve WinDev, WebDev, WinDev Mobile
- **WLanguage**: Linguagem de programação proprietária (sintaxe similar a BASIC/Pascal)
- **HyperFile**: Banco de dados proprietário (pode exportar para SQL)

### Tipos de Elementos WinDev
| Extensão | Código | Tipo | Camada |
|----------|--------|------|--------|
| .wwp/.wdp | 4097/1 | Projeto | - |
| .wwh | 65538 | Página Web | UI |
| .wwt | 65541 | Template de Página | UI |
| .wwn | 65539 | Browser Procedures (JS) | UI |
| .wdg | 7 | Grupo de Procedures (Server) | Business |
| .wdc | 4 | Classe | Domain |
| .WDR | 5 | Query SQL | Schema |
| .wdrest | - | API REST | API |
| .wdsdl | 22 | Webservice WSDL | API |
| .wdd/.wda | - | Análise (modelo de dados) | Schema |
| .wde | - | Relatório | UI |
| .wdw | - | Window (WinDev) | UI |

### Controles de UI (Controls)
- Identificados por `type_code` numérico no arquivo .wwh
- Prefixos padrão: EDT_ (Edit), BTN_ (Button), TABLE_ (Table), CELL_ (Cell)
- Hierarquia: Containers (CELL, ZONE, POPUP) podem ter filhos
- Eventos principais:
  - 851984: OnClick (Server)
  - 851998: OnClick (Browser)
  - 851999: OnOpen/OnDisplay
  - 852015: OnChange
  - 851995: OnRowSelect

### Mapeamento WLanguage → Python

#### Tipos de Dados
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

#### Estruturas de Controle
| WLanguage | Python |
|-----------|--------|
| IF...THEN...ELSE...END | if...elif...else |
| SWITCH...CASE...END | match...case (3.10+) |
| FOR i = 1 TO n | for i in range(1, n+1) |
| FOR EACH...END | for item in iterable |
| WHILE...END | while |
| LOOP...END | while True: ... break |
| RESULT | return |

#### Funções Comuns
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

## MongoDB Schema

### Collections
- `projects`: Metadados do projeto WinDev
- `elements`: Páginas, procedures, classes, queries (documentos pai)
- `controls`: Controles de UI extraídos das páginas
- `control_types`: Tabela dinâmica de tipos de controles
- `procedures`: (futuro) Procedures extraídas de .wdg

### Element Schema
```javascript
{
  _id: ObjectId,
  project_id: ObjectId,
  source_type: "page" | "procedure" | "class" | "query" | "report",
  source_name: "PAGE_Login",
  source_file: "PAGE_Login.wwh",
  windev_type: 65538,

  // AST/IR
  ast: { procedures: [], variables: [], controls: [], events: [] },

  // Dependências
  dependencies: {
    uses: ["ServerProcedures", "classUsuario"],
    usedBy: ["PAGE_PRINCIPAL"],
    dataFiles: ["USUARIO", "CLIENTE"],
    externalAPIs: ["APIFitbank"]
  },

  // Conversão
  conversion: {
    status: "pending" | "in_progress" | "converted" | "validated",
    targetStack: "fastapi-jinja2",
    targetFiles: [],
    issues: []
  },

  topological_order: 15,
  layer: "ui",
  controls_count: 42
}
```

### Control Schema
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
  properties: { height: 24, width: 200, visible: true },
  events: [{ type_code: 851984, code: "..." }],
  is_container: false,
  has_code: true
}
```

## CLI Commands

```bash
# Importar projeto WinDev (streaming para arquivos grandes)
wxcode import ./Projeto.wwp --batch-size 100

# Dividir PDF de documentação em arquivos individuais por elemento
wxcode split-pdf ./Documentation_Projeto.pdf --output ./output/pdf_docs

# Enriquecer elementos com controles e propriedades
wxcode enrich ./caminho/projeto --pdf-docs ./output/pdf_docs

# Analisar dependências (futuro)
wxcode analyze --project nome_projeto --build-graph

# Converter por camada (futuro)
wxcode convert --project nome_projeto --layer schema|domain|business|api|ui

# Validar conversão (futuro)
wxcode validate --project nome_projeto --generate-tests

# Exportar projeto convertido (futuro)
wxcode export --project nome_projeto --output ./projeto-python
```

## Important Constraints

### Technical Constraints
- Arquivos .wwh/.wdw são UTF-8 com estrutura proprietária (não XML/JSON)
- Arquivos .wdg são YAML-like com blocos de código usando `|1+`
- PDFs de documentação contêm propriedades visuais dos controles
- Alguns type_codes são ambíguos (ex: type_code=2 pode ser Edit ou Column)
- Procedures locais estão embutidas no arquivo da página (.wwh)

### Performance Constraints
- Projetos WinDev podem ter centenas de páginas
- Arquivos .wwp podem ter 100.000+ linhas
- Usar streaming e batch processing para evitar memory issues
- Batch size padrão: 100 documentos por operação MongoDB

### Business Constraints
- Conversão deve preservar lógica de negócio original
- Nomes de variáveis/funções devem ser mantidos quando possível
- Comentários originais devem ser preservados

## External Dependencies

### MongoDB
- **Host**: Configurável via environment ou .mcp.json
- **Database**: `wxcode`
- **Collections**: `projects`, `elements`, `controls`, `control_types`

### Projeto de Referência
- **Path**: `project-refs/Linkpay_ADM/`
- **Tipo**: Projeto WebDev 26 real
- **Elementos**: ~100 páginas, ~50 procedure groups, classes, queries
- **Uso**: Desenvolvimento, testes, validação de parsers

### Claude API
- Usado para conversão inteligente de código WLanguage → Python
- Chunking semântico para elementos grandes (>4000 tokens)

### Key Files Reference
| Arquivo | Descrição |
|---------|-----------|
| `CLAUDE.md` | Contexto do projeto para Claude |
| `docs/ROADMAP.md` | Prompts detalhados para cada fase |
| `project-refs/WX_CodeStyle_Prefixes.md` | Prefixos padrão WinDev/WebDev |

---

## OpenSpec Workflow

### IMPORTANTE: Sempre usar Skills, não CLI direta

Ao trabalhar com OpenSpec, **SEMPRE** use as skills disponíveis em vez de executar comandos `openspec` diretamente:

| Ação | Skill (USAR) | CLI (NÃO USAR) |
|------|--------------|----------------|
| Criar proposta | `/openspec:proposal` | ~~`openspec proposal`~~ |
| Aplicar mudanças | `/openspec:apply` | ~~`openspec apply`~~ |
| Arquivar change | `/openspec:archive` | ~~`openspec archive`~~ |

**Por que usar Skills?**
- Skills contêm instruções detalhadas e guardrails
- Garantem consistência no workflow
- Incluem validações automáticas
- Seguem as convenções do projeto

**Comandos CLI permitidos (apenas para consulta):**
```bash
openspec list          # Listar changes
openspec show <id>     # Ver detalhes de uma change
openspec validate      # Validar specs
```

## Task Generation Guidelines

When creating tasks for change proposals:
- Optimize for Claude Sonnet 4.5 capabilities
- Break down into smaller, focused tasks (max 3-5 steps each)
- Each task should be completable in a single prompt
- Avoid tasks that require extensive context switching
- Include clear acceptance criteria in each task
- Prefer explicit file paths over vague references

### Post-Proposal Reminder
After generating a proposal, always remind the user:
> 💡 **Dica:** Antes de executar `/openspec:apply`, confirme que está usando Sonnet 4.5:
> - Verifique com `/status`
> - Ou troque com `/model sonnet`

