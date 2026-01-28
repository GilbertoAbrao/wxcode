# Arquitetura do WXCODE

## Visão Geral

O wxcode é um sistema de conversão de projetos WinDev/WebDev/WinDev Mobile para stacks modernas. A arquitetura foi projetada para:

1. **Preservar conhecimento** - Toda lógica de negócio deve ser mantida
2. **Conversão inteligente** - Uso de LLM para conversões complexas
3. **Rastreabilidade** - Manter relacionamento entre código original e convertido
4. **Extensibilidade** - Suportar múltiplas stacks de destino

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              WXCODE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                         CLI (Typer)                               │   │
│  │  wxcode import | analyze | plan | convert | validate | export │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      FastAPI Application                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │   │
│  │  │ /projects   │  │ /elements   │  │ /conversions            │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌─────────────────────────────────┴────────────────────────────────┐   │
│  │                         Core Services                             │   │
│  │                                                                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │   │
│  │  │   Parser    │  │  Analyzer   │  │      Converter          │   │   │
│  │  │  ─────────  │  │  ─────────  │  │   ─────────────────     │   │   │
│  │  │ .wwp parser │  │ Dependency  │  │ Schema Converter        │   │   │
│  │  │ .wwh parser │  │ Graph       │  │ Model Converter         │   │   │
│  │  │ .wdg parser │  │ Pattern     │  │ Route Converter         │   │   │
│  │  │ .wdc parser │  │ Detection   │  │ Template Converter      │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘   │   │
│  │                                                                   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌─────────────────────────────────┴────────────────────────────────┐   │
│  │                      LLM Integration                              │   │
│  │  ┌───────────────────────────────────────────────────────────┐   │   │
│  │  │  Claude API (Anthropic)                                    │   │   │
│  │  │  - AST/IR Generation                                       │   │   │
│  │  │  - Code Conversion                                         │   │   │
│  │  │  - Pattern Recognition                                     │   │   │
│  │  └───────────────────────────────────────────────────────────┘   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌─────────────────────────────────┴────────────────────────────────┐   │
│  │                         Data Layer                                │   │
│  │  ┌───────────────────────────────────────────────────────────┐   │   │
│  │  │  MongoDB (via Beanie ODM)                                  │   │   │
│  │  │  - Projects                                                │   │   │
│  │  │  - Elements                                                │   │   │
│  │  │  - Conversions                                             │   │   │
│  │  └───────────────────────────────────────────────────────────┘   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Componentes

### 1. CLI (Typer)

Interface de linha de comando para operações de conversão.

**Comandos:**
- `import` - Importa projeto WinDev para MongoDB
- `split-pdf` - Divide PDF de documentação em arquivos individuais
- `enrich` - Enriquece elementos com controles, eventos, procedures locais e queries
- `parse-procedures` - Parseia procedures de arquivos .wdg
- `parse-schema` - Parseia schema do banco (Analysis .xdd)
- `parse-classes` - Parseia classes (.wdc)
- `analyze` - Analisa dependências, detecta ciclos, calcula ordem topológica
- `plan` - Gera plano de conversão
- `convert` - Executa conversão por camada
- `validate` - Valida código convertido
- `export` - Exporta projeto convertido

### 2. FastAPI Application

API REST para integração e interface web.

**Endpoints:**
- `/projects` - CRUD de projetos
- `/elements` - Elementos do projeto
- `/conversions` - Status e controle de conversões

### 3. Parser

Responsável por ler e interpretar arquivos WinDev.

**Parsers de Arquivos:**
- `wwp_parser` - Arquivo de projeto (.wwp/.wdp)
- `wwh_parser` - Páginas web e windows (.wwh/.wdw)
- `wdg_parser` - Grupos de procedures (.wdg)
- `wdc_parser` - Classes (.wdc)
- `xdd_parser` - Schema do banco (Analysis .xdd)

**Parsers de PDF (Documentação):**
- `pdf_doc_splitter` - Divide PDF em elementos individuais (pages, windows, queries)
- `pdf_element_parser` - Extrai propriedades visuais de controles
- `query_parser` - Extrai SQL, parâmetros e tabelas das queries

**Enrichers:**
- `element_enricher` - Enriquece pages/windows com controles, eventos e procedures locais
- `query_enricher` - Enriquece queries com SQL extraído do PDF

### 4. Analyzer

Analisa o código extraído para entender estrutura e dependências.

**Componentes:**
- `graph_builder` - Constrói grafo NetworkX de dependências
- `cycle_detector` - Detecta ciclos e sugere pontos de quebra
- `topological_sorter` - Ordena elementos por camadas para conversão
- `dependency_analyzer` - Orquestrador (CLI `analyze`)
- `graph_exporter` - Exporta para DOT (Graphviz) e HTML (vis.js)

**Funcionalidades:**
- Construção do grafo de dependências (tabelas, classes, procedures, pages, queries)
- Detecção de ciclos com sugestões de quebra
- Cálculo da ordem topológica por camadas
- Persistência de `topological_order` e `layer` nos documentos
- Exportação para visualização (DOT, HTML interativo)

### 5. Converter

Converte código WLanguage para a stack alvo.

**Conversores por camada:**
- `schema_converter` - Modelo de dados → SQLAlchemy/Pydantic
- `model_converter` - Classes → Python classes
- `service_converter` - Procedures → Services
- `route_converter` - REST endpoints → FastAPI routes
- `template_converter` - Pages → Jinja2 templates

### 6. LLM Integration

Integração com Claude para conversões inteligentes.

**Usos:**
- Geração de AST/IR a partir de código WLanguage
- Conversão de lógica complexa
- Detecção de padrões e intenções
- Geração de testes

## Fluxo de Dados

```
Projeto WinDev (.wwp)
        │
        ▼
┌───────────────────┐
│      Parser       │ ──── Lê e extrai elementos
└───────────────────┘
        │
        ▼
┌───────────────────┐
│     MongoDB       │ ──── Armazena elementos e metadados
└───────────────────┘
        │
        ▼
┌───────────────────┐
│     Analyzer      │ ──── Constrói grafo, detecta padrões
└───────────────────┘
        │
        ▼
┌───────────────────┐
│    Converter      │ ──── Converte por camada (topológico)
│   + LLM (Claude)  │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│     Validator     │ ──── Valida sintaxe, gera testes
└───────────────────┘
        │
        ▼
┌───────────────────┐
│     Exporter      │ ──── Gera projeto FastAPI + Jinja2
└───────────────────┘
        │
        ▼
Projeto Python (FastAPI)
```

## Modelo de Dados (MongoDB)

### Collection: projects
```javascript
{
  _id: ObjectId,
  name: string,
  sourcePath: string,
  windevVersion: number,
  configurations: [...],
  createdAt: datetime,
  status: "imported" | "analyzed" | "converting" | "converted"
}
```

### Collection: elements
```javascript
{
  _id: ObjectId,
  projectId: ObjectId,
  sourceType: "page" | "window" | "report" | "query" | "class" | "procedure_group",
  sourceName: string,
  sourceFile: string,
  rawContent: string,
  chunks: [...],
  ast: {
    procedures: [...],
    variables: [...],
    controls: [...],
    events: [...],
    // Para queries:
    sql: string,
    parameters: [...],
    tables: [...],
    incomplete: boolean
  },
  dependencies: {
    uses: [...],
    usedBy: [...],
    dataFiles: [...],
    externalAPIs: [...]
  },
  conversion: {...},
  topologicalOrder: number,
  layer: string
}
```

### Collection: controls
```javascript
{
  _id: ObjectId,
  element_id: ObjectId,
  project_id: ObjectId,
  type_code: number,
  name: string,
  full_path: string,
  parent_control_id: ObjectId,
  children_ids: [ObjectId],
  depth: number,
  properties: {...},
  events: [...],
  is_container: boolean,
  has_code: boolean
}
```

### Collection: procedures
```javascript
{
  _id: ObjectId,
  project_id: ObjectId,
  element_id: ObjectId,  // Se procedure local
  name: string,
  is_global: boolean,
  visibility: "public" | "private" | "protected",
  parameters: [...],
  return_type: string,
  code: string,
  dependencies: {...}
}
```

### Collection: class_definitions
```javascript
{
  _id: ObjectId,
  project_id: ObjectId,
  name: string,
  parent_class: string,
  is_abstract: boolean,
  members: [...],
  methods: [...],
  constants: [...]
}
```

### Collection: schemas
```javascript
{
  _id: ObjectId,
  project_id: ObjectId,
  name: string,
  tables: [{
    name: string,
    columns: [...],
    primary_key: [...],
    indexes: [...]
  }],
  connections: [...]
}
```

### Collection: conversions
```javascript
{
  _id: ObjectId,
  projectId: ObjectId,
  targetStack: string,
  status: string,
  startedAt: datetime,
  completedAt: datetime,
  elementsTotal: number,
  elementsConverted: number,
  errors: [...]
}
```

## Extensibilidade

### Adicionando Nova Stack de Destino

1. Criar pasta `converter/<stack_name>/`
2. Implementar conversores por camada:
   - `schema_converter.py`
   - `model_converter.py`
   - `service_converter.py`
   - `route_converter.py`
   - `template_converter.py`
3. Registrar no factory de conversores
4. Criar skill correspondente em `skills/wx-to-<stack>.md`

### Adicionando Novo Parser

1. Criar `parser/<extensao>_parser.py`
2. Implementar interface `BaseParser`
3. Registrar no factory de parsers
