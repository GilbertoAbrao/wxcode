# Handoff: Integração da Knowledge Base com Workflow GSD

**Data**: 2025-01-21
**Origem**: Conversa no projeto Linkpay_ADM
**Objetivo**: Implementar MCP Server para integrar KB (MongoDB + Neo4j) no workflow de conversão Windev/Webdev

---

## Contexto

O usuário possui uma **Knowledge Base já construída** com:

1. **MongoDB**: Codebase Windev/Webdev "explodida" - definições de telas, código, regras de negócio
2. **Neo4j**: Grafo de dependências entre telas/componentes com ordem topológica
3. **Granularidade**: Nível de controle de tela

Esta KB representa o trabalho de engenharia reversa do sistema legado e é o ativo principal para guiar a conversão de stack.

---

## Decisão de Arquitetura: MCP Server com FastAPI

### Por que MCP Server?

- Integração nativa com Claude Code e workflow GSD
- Consultas dinâmicas durante planejamento e execução
- Permite que os agentes GSD consultem a KB automaticamente

### Por que FastAPI (não TypeScript)?

- **Consistência**: Todo o projeto wxcode já é FastAPI + Python
- **Reuso**: Pode reaproveitar models Beanie/Pydantic existentes
- **Manutenção**: Uma única linguagem para todo o projeto
- **Biblioteca**: Existe `mcp` SDK para Python (fastmcp)

### Tools Propostos para o MCP Server

| Tool | Descrição | Fonte |
|------|-----------|-------|
| `get_element_definition` | Retorna definição completa de um elemento (código, controles, eventos) | MongoDB |
| `get_controls` | Lista controles de um elemento com hierarquia e propriedades | MongoDB |
| `get_dependencies` | Lista dependências de um elemento | Neo4j/MongoDB |
| `get_topological_order` | Ordem de conversão para um conjunto de elementos | Neo4j |
| `get_conversion_candidates` | Próximos elementos prontos para converter (deps já convertidas) | Neo4j |
| `search_code_patterns` | Busca padrões específicos no código legado | MongoDB |
| `get_schema` | Schema/entidades relacionadas a um elemento | MongoDB |
| `mark_as_converted` | Marca um elemento como convertido | MongoDB/Neo4j |
| `get_procedures` | Lista procedures de um elemento ou globais | MongoDB |

### Fluxo de Integração

```
┌─────────────────────────────────────────────────────────────┐
│                    /gsd:new-milestone                        │
│  "Converter Módulo X"                                        │
│                                                              │
│  1. Consulta KB: quais elementos pertencem ao módulo?       │
│  2. Consulta Neo4j: ordem topológica desses elementos       │
│  3. Gera phases automaticamente baseado na ordem            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    /gsd:plan-phase                           │
│  "Converter PAGE_Login"                                      │
│                                                              │
│  1. Consulta KB: definição completa da página               │
│  2. Consulta KB: controles e eventos                        │
│  3. Consulta KB: dependências (procedures, queries, etc)    │
│  4. Gera PLAN.md com mapeamento Windev → FastAPI+Jinja2     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    /gsd:execute-phase                        │
│                                                              │
│  Durante execução, consulta KB para:                        │
│  - Código original da página                                │
│  - Regras de negócio nos eventos                           │
│  - Validações e tratamentos de erro                        │
└─────────────────────────────────────────────────────────────┘
```

---

## RESPOSTAS: Estrutura MongoDB

### Collections Principais

| Collection | Model | Descrição |
|------------|-------|-----------|
| `elements` | `Element` | Páginas, procedures, classes, queries |
| `controls` | `Control` | Controles UI de cada elemento |
| `procedures` | `Procedure` | Procedures globais e locais |
| `schemas` | `DatabaseSchema` | Schema do banco (tabelas, colunas) |
| `projects` | `Project` | Projetos importados |
| `control_types` | `ControlTypeDefinition` | Definições de tipos de controle |

### Schema: Element (collection: `elements`)

```python
{
    "_id": ObjectId,
    "project_id": DBRef(Project),

    # Identificação WinDev
    "source_type": "page" | "procedure_group" | "class" | "query" | "report" | ...,
    "source_name": "PAGE_Login",
    "source_file": "PAGE_Login.wwh",
    "windev_type": 65538,
    "identifier": "abc123...",  # ID hexadecimal WinDev

    # Conteúdo
    "raw_content": "...",  # Código fonte completo
    "chunks": [  # Para elementos grandes
        {"index": 0, "content": "...", "tokens": 3500, "semantic_type": "GLOBAL"}
    ],

    # AST/IR parseado
    "ast": {
        "procedures": [...],
        "variables": [...],
        "controls": [...],
        "events": [...],
        "queries": [...],
        "imports": [...],
        "exports": [...]
    },

    # Dependências
    "dependencies": {
        "uses": ["ServerProcedures", "classUsuario"],
        "used_by": ["PAGE_PRINCIPAL"],
        "data_files": ["USUARIO", "CLIENTE"],
        "external_apis": ["APIFitbank"],
        "bound_tables": ["USUARIO"]  # Via DataBinding de controles
    },

    # Status de conversão
    "conversion": {
        "status": "pending" | "in_progress" | "converted" | "validated",
        "target_stack": "fastapi-jinja2",
        "target_files": [...],
        "issues": [],
        "human_review_required": false
    },

    # Ordenação
    "topological_order": 15,
    "layer": "schema" | "domain" | "business" | "api" | "ui",

    # Timestamps
    "created_at": datetime,
    "updated_at": datetime
}
```

### Schema: Control (collection: `controls`)

```python
{
    "_id": ObjectId,
    "element_id": ObjectId,  # PAGE_Login
    "project_id": ObjectId,

    # Tipo
    "type_code": 8,  # Código WinDev (8 = Edit)
    "type_definition_id": ObjectId,

    # Identificação
    "name": "EDT_LOGIN",
    "full_path": "CELL_NoName1.EDT_LOGIN",

    # Hierarquia
    "parent_control_id": ObjectId,
    "children_ids": [ObjectId],
    "depth": 1,

    # Propriedades visuais (do PDF)
    "properties": {
        "height": 24,
        "width": 200,
        "x_position": 100,
        "y_position": 50,
        "visible": true,
        "enabled": true,
        "input_type": "Text",
        "caption": "Login",
        "required": false
    },

    # Eventos com código
    "events": [
        {
            "type_code": 851994,
            "event_name": "OnClick",
            "code": "...",
            "role": "S"  # S=Server, B=Browser
        }
    ],

    # Data Binding
    "data_binding": {
        "binding_type": "simple",  # simple | complex | variable
        "table_name": "USUARIO",
        "field_name": "login"
    },
    "is_bound": true,

    # Flags
    "is_orphan": false,  # Existe no .wwh mas não no PDF
    "is_container": false,
    "has_code": true
}
```

### Schema: Procedure (collection: `procedures`)

```python
{
    "_id": ObjectId,
    "element_id": ObjectId,  # .wdg ou PAGE pai
    "project_id": ObjectId,

    # Identificação
    "name": "ValidaCPF",
    "procedure_id": "...",

    # Assinatura
    "parameters": [
        {"name": "sCPF", "type": "string", "is_local": false}
    ],
    "return_type": "boolean",

    # Código
    "code": "...",
    "code_lines": 45,

    # Dependências
    "dependencies": {
        "calls_procedures": ["FormataCPF", "HTTPSend"],
        "uses_files": ["CLIENTE"],
        "uses_apis": ["APIReceita"],
        "uses_queries": []
    },

    # Metadados
    "is_public": true,
    "is_local": false,  # true = procedure local de página
    "scope": null,  # "page" | "window" | null (global)
    "has_error_handling": true
}
```

### Schema: DatabaseSchema (collection: `schemas`)

```python
{
    "_id": ObjectId,
    "project_id": ObjectId,
    "source_file": "Linkpay_ADM.xdd",

    # Conexões
    "connections": [
        {
            "name": "CNX_BASE_HOMOLOG",
            "type_code": 1,
            "database_type": "sqlserver",
            "source": "servidor.database.net",
            "port": "1433",
            "database": "LinkpayDB"
        }
    ],

    # Tabelas
    "tables": [
        {
            "name": "USUARIO",
            "physical_name": "tbl_usuario",
            "connection_name": "CNX_BASE_HOMOLOG",
            "columns": [
                {
                    "name": "id",
                    "hyperfile_type": 4,
                    "python_type": "int",
                    "is_primary_key": true,
                    "is_auto_increment": true
                },
                {
                    "name": "login",
                    "hyperfile_type": 1,
                    "python_type": "str",
                    "size": 50
                }
            ],
            "indexes": [...]
        }
    ]
}
```

---

## RESPOSTAS: Schema Neo4j

### Labels (Node Types)

| Label | Fonte MongoDB | Propriedades Principais |
|-------|---------------|------------------------|
| `Page` | Element (source_type=page) | name, project, layer, mongo_id, topological_order |
| `Window` | Element (source_type=window) | name, project, layer, mongo_id, topological_order |
| `Query` | Element (source_type=query) | name, project, layer, mongo_id |
| `Procedure` | Procedure | name, project, layer, mongo_id, is_public, is_local, scope |
| `Class` | ClassDefinition | name, project, layer, mongo_id, inherits_from, is_abstract |
| `Table` | DatabaseSchema.tables | name, project, layer, physical_name, connection |

### Relationships

| Tipo | Origem → Destino | Descrição |
|------|------------------|-----------|
| `:CALLS` | Page/Window → Procedure | Página chama procedure |
| `:CALLS` | Procedure → Procedure | Procedure chama outra |
| `:USES_TABLE` | Page/Window/Class/Procedure → Table | Acessa tabela |
| `:USES_CLASS` | Class → Class | Usa outra classe (composição) |
| `:INHERITS` | Class → Class | Herda de classe pai |

### Queries Cypher Existentes

```cypher
-- Ordem topológica de elementos não convertidos
MATCH (s:Page)
WHERE s.project = $project AND s.converted = false
WITH s
MATCH path = (s)-[:CALLS*0..]->(dep)
WITH s, max(length(path)) as depth
RETURN s.name, depth
ORDER BY depth ASC

-- Análise de impacto: o que é afetado se X mudar?
MATCH (source {name: $name})
OPTIONAL MATCH path = (source)<-[*1..5]-(affected)
WHERE affected <> source
WITH source, affected, min(length(path)) as depth
RETURN affected.name, labels(affected)[0] as type, depth

-- Encontrar hubs (nós críticos)
MATCH (n)
WHERE n.project = $project
WITH n, COUNT{(n)<--()} as incoming, COUNT{(n)-->()} as outgoing
WHERE incoming + outgoing >= $min
RETURN n.name, labels(n)[0] as type, incoming, outgoing
ORDER BY incoming + outgoing DESC

-- Código morto (procedures não chamadas)
MATCH (n:Procedure)
WHERE NOT ()-[:CALLS]->(n)
AND NOT n.name STARTS WITH 'API'
AND NOT n.name STARTS WITH 'Task'
RETURN n.name

-- Caminho entre dois elementos
MATCH (a {name: $source})
MATCH (b {name: $target})
MATCH path = shortestPath((a)-[*]-(b))
RETURN path
```

---

## RESPOSTAS: APIs REST Existentes

O projeto já possui uma API FastAPI em `src/wxcode/api/`:

| Endpoint | Arquivo | Descrição |
|----------|---------|-----------|
| `GET /elements/` | elements.py | Lista elementos por projeto |
| `GET /elements/{id}` | elements.py | Detalhe de elemento |
| `GET /elements/by-name/{project}/{name}` | elements.py | Busca por nome |
| `GET /projects/` | projects.py | Lista projetos |
| `POST /import/` | import_wizard.py | Importa projeto |
| `WS /ws/import/` | import_wizard_ws.py | WebSocket para import |
| `GET /tree/{project}/{element}` | tree.py | Árvore de controles |

**Base URL**: `http://localhost:8000`

---

## RESPOSTAS: Localização MongoDB/Neo4j

### Desenvolvimento Local

```bash
# Via docker-compose.yml
docker-compose up -d mongodb neo4j

# MongoDB
# - URL: mongodb://localhost:27017
# - Database: wxcode

# Neo4j
# - Bolt: bolt://localhost:7687
# - Browser: http://localhost:7474
# - Auth: neo4j/password
```

### Produção (EasyPanel)

```bash
# .env.example mostra configuração de produção
# Neo4j: bolt://5.161.216.182:7687
# MongoDB: conexão Atlas ou servidor próprio
```

### Configuração (src/wxcode/config.py)

```python
# MongoDB
mongodb_url: str = "mongodb://localhost:27017"
mongodb_database: str = "wxcode"

# Neo4j
neo4j_uri: str = "bolt://localhost:7687"
neo4j_user: str = "neo4j"
neo4j_password: str = ""
neo4j_database: str = "neo4j"
```

---

## Arquitetura do MCP Server (FastAPI)

### Estrutura Proposta

```
src/wxcode/mcp/
├── __init__.py
├── server.py           # FastMCP server setup
├── tools/
│   ├── __init__.py
│   ├── elements.py     # get_element_definition, get_controls
│   ├── dependencies.py # get_dependencies, get_topological_order
│   ├── conversion.py   # get_conversion_candidates, mark_as_converted
│   ├── search.py       # search_code_patterns
│   └── schema.py       # get_schema, get_procedures
└── resources/
    ├── __init__.py
    └── project.py      # Resource para listar projetos/elementos
```

### Implementação Base

```python
# src/wxcode/mcp/server.py
from mcp.server.fastmcp import FastMCP
from wxcode.config import get_settings
from wxcode.models import Element, Control, Procedure

mcp = FastMCP("windev-kb")

@mcp.tool()
async def get_element_definition(
    project_name: str,
    element_name: str
) -> dict:
    """
    Retorna definição completa de um elemento (página, classe, etc).

    Inclui: código fonte, AST, dependências, status de conversão.
    """
    from wxcode.models import Project

    project = await Project.find_one(Project.name == project_name)
    if not project:
        return {"error": f"Projeto não encontrado: {project_name}"}

    element = await Element.find_one(
        {"project_id.$id": project.id},
        Element.source_name == element_name
    )
    if not element:
        return {"error": f"Elemento não encontrado: {element_name}"}

    return {
        "name": element.source_name,
        "type": element.source_type.value,
        "layer": element.layer.value if element.layer else None,
        "raw_content": element.raw_content,
        "ast": element.ast.model_dump() if element.ast else None,
        "dependencies": element.dependencies.model_dump(),
        "conversion_status": element.conversion.status.value,
        "topological_order": element.topological_order
    }

@mcp.tool()
async def get_controls(
    project_name: str,
    element_name: str,
    include_events: bool = True
) -> dict:
    """
    Lista controles de um elemento com hierarquia.

    Retorna árvore de controles com propriedades e eventos.
    """
    from wxcode.models import Project

    project = await Project.find_one(Project.name == project_name)
    element = await Element.find_one(
        {"project_id.$id": project.id},
        Element.source_name == element_name
    )

    controls = await Control.find(
        Control.element_id == element.id
    ).sort("+depth", "+name").to_list()

    return {
        "element": element_name,
        "total_controls": len(controls),
        "controls": [
            {
                "name": c.name,
                "type_code": c.type_code,
                "full_path": c.full_path,
                "depth": c.depth,
                "properties": c.properties.model_dump() if c.properties else None,
                "events": [e.model_dump() for e in c.events] if include_events else [],
                "data_binding": c.data_binding.model_dump() if c.data_binding else None
            }
            for c in controls
        ]
    }

@mcp.tool()
async def get_conversion_candidates(
    project_name: str,
    limit: int = 10
) -> dict:
    """
    Retorna próximos elementos prontos para converter.

    Elementos cujas dependências já foram convertidas.
    """
    from wxcode.graph.neo4j_connection import Neo4jConnection
    from wxcode.config import get_settings

    settings = get_settings()
    conn = Neo4jConnection(
        settings.neo4j_uri,
        settings.neo4j_user,
        settings.neo4j_password
    )
    await conn.connect()

    result = await conn.execute("""
        MATCH (s:Page {project: $project})
        WHERE NOT EXISTS {
            MATCH (s)-[:CALLS]->(dep:Procedure)
            WHERE NOT EXISTS {
                MATCH (p2:Page)-[:CALLS]->(dep)
                WHERE p2.converted = true
            }
        }
        AND s.converted = false
        RETURN s.name as name, s.topological_order as order
        ORDER BY s.topological_order ASC
        LIMIT $limit
    """, {"project": project_name, "limit": limit})

    await conn.close()

    return {
        "candidates": [
            {"name": r["name"], "topological_order": r["order"]}
            for r in result
        ]
    }

# Executar standalone ou integrar com FastAPI existente
if __name__ == "__main__":
    mcp.run()
```

### Configuração no Claude Code

```json
// .mcp.json
{
  "mcpServers": {
    "windev-kb": {
      "command": "python",
      "args": ["-m", "wxcode.mcp.server"],
      "cwd": "/Users/gilberto/projetos/wxk/wxcode"
    }
  }
}
```

---

## Próximos Passos

1. [ ] **Criar módulo MCP** (`src/wxcode/mcp/`)
   - Instalar dependência: `pip install mcp`
   - Estruturar server.py com FastMCP

2. [ ] **Implementar Tools básicos**
   - `get_element_definition`
   - `get_controls`
   - `get_dependencies`

3. [ ] **Implementar Tools de conversão**
   - `get_conversion_candidates`
   - `get_topological_order`
   - `mark_as_converted`

4. [ ] **Configurar no Claude Code**
   - Adicionar ao `.mcp.json`
   - Testar integração

5. [ ] **Integrar com GSD workflow**
   - Customizar prompts das phases
   - Criar templates de milestone para conversão

---

## Referências

- Projeto: `/Users/gilberto/projetos/wxk/wxcode`
- Models: `src/wxcode/models/`
- Graph: `src/wxcode/graph/`
- API existente: `src/wxcode/api/`
- MCP SDK Python: https://github.com/modelcontextprotocol/python-sdk
- FastMCP: https://gofastmcp.com/
