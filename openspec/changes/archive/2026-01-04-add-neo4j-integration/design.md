# Design: Neo4j Integration

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ARQUITETURA HÍBRIDA                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     MongoDB (Source of Truth)                       │    │
│  │  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌─────────┐            │    │
│  │  │ schemas  │ │class_defini- │ │procedures│ │elements │            │    │
│  │  │          │ │   tions      │ │          │ │(pages)  │            │    │
│  │  └──────────┘ └──────────────┘ └──────────┘ └─────────┘            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│                         ┌─────────────────────┐                             │
│                         │  Neo4jSyncService   │                             │
│                         │  (wxcode sync)   │                             │
│                         └─────────────────────┘                             │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                          Neo4j (Analytics)                          │    │
│  │                                                                     │    │
│  │   (:Table)─[:USES]─►(:Procedure)─[:CALLS]─►(:Procedure)            │    │
│  │                          │                                          │    │
│  │                          ▼                                          │    │
│  │                     (:Page)───[:USES]───►(:Class)                   │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                     ┌──────────────┴──────────────┐                         │
│                     ▼                              ▼                        │
│            ┌─────────────────┐            ┌─────────────────┐               │
│            │ Neo4j Browser   │            │  CLI Commands   │               │
│            │ (Visualização)  │            │ (wxcode      │               │
│            │                 │            │  impact, path)  │               │
│            └─────────────────┘            └─────────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Neo4j Data Model

### Node Labels

| Label | Properties | MongoDB Source |
|-------|------------|----------------|
| `:Table` | name, layer, topological_order | schemas.tables[] |
| `:Class` | name, layer, topological_order, inherits_from, mongo_id | class_definitions |
| `:Procedure` | name, layer, topological_order, is_public, mongo_id | procedures |
| `:Page` | name, layer, topological_order, mongo_id | elements (source_type=page) |
| `:Window` | name, layer, topological_order, mongo_id | elements (source_type=window) |
| `:Query` | name, layer, mongo_id | elements (source_type=query) |

### Relationship Types

| Type | From | To | Properties |
|------|------|----|----|
| `:INHERITS` | Class | Class | - |
| `:USES_CLASS` | Procedure, Page | Class | - |
| `:CALLS` | Procedure | Procedure | - |
| `:USES_TABLE` | Procedure, Class, Page | Table | - |
| `:USES_QUERY` | Procedure, Page | Query | - |

### Example Graph

```cypher
// Estrutura típica
(:Table {name: "CLIENTE"})
    ^
    |[:USES_TABLE]
    |
(:Class {name: "classCliente", layer: "domain"})
    ^
    |[:USES_CLASS]
    |
(:Procedure {name: "CadastrarCliente", layer: "business"})
    ^
    |[:CALLS]
    |
(:Page {name: "PAGE_Cliente", layer: "ui"})
```

## Component Design

### Neo4jConnection

```python
# src/wxcode/graph/neo4j_connection.py

class Neo4jConnection:
    """
    Gerencia conexão com Neo4j.

    Configuração via settings ou environment:
    - NEO4J_URI: bolt://localhost:7687
    - NEO4J_USER: neo4j
    - NEO4J_PASSWORD: ****
    """

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    async def execute(self, query: str, parameters: dict = None) -> list:
        """Executa query Cypher."""
        ...

    async def batch_create(self, nodes: list[dict], batch_size: int = 1000):
        """Cria nós em batch para performance."""
        ...
```

### Neo4jSyncService

```python
# src/wxcode/graph/neo4j_sync.py

class Neo4jSyncService:
    """
    Sincroniza grafo do MongoDB para Neo4j.
    """

    async def sync_project(self, project_id: ObjectId) -> SyncResult:
        """
        Sincroniza projeto completo.

        1. Limpa dados existentes do projeto no Neo4j
        2. Cria nós para cada elemento
        3. Cria relacionamentos baseado em dependencies
        4. Valida contagens
        """
        ...

    async def _create_table_nodes(self, schema: DatabaseSchema) -> int:
        """Cria nós :Table."""
        ...

    async def _create_class_nodes(self, classes: list[ClassDefinition]) -> int:
        """Cria nós :Class e relacionamentos :INHERITS."""
        ...

    async def _create_procedure_nodes(self, procedures: list[Procedure]) -> int:
        """Cria nós :Procedure e relacionamentos :CALLS, :USES_TABLE."""
        ...

    async def _create_page_nodes(self, pages: list[Element]) -> int:
        """Cria nós :Page e relacionamentos :USES_*."""
        ...
```

### ImpactAnalyzer

```python
# src/wxcode/graph/impact_analyzer.py

class ImpactAnalyzer:
    """
    Análise de impacto usando Neo4j.
    """

    async def get_impact(
        self,
        node_id: str,
        max_depth: int = 5
    ) -> ImpactResult:
        """
        Retorna todos os elementos afetados por mudança em node_id.

        Query Cypher:
        MATCH (source {name: $name})<-[*1..{max_depth}]-(affected)
        RETURN affected.name, labels(affected), length(path) as depth
        ORDER BY depth
        """
        ...

    async def get_path(
        self,
        source: str,
        target: str
    ) -> list[PathResult]:
        """
        Retorna caminhos entre dois nós.

        Query Cypher:
        MATCH path = shortestPath((a)-[*]-(b))
        WHERE a.name = $source AND b.name = $target
        RETURN path
        """
        ...

    async def find_hubs(self, min_connections: int = 10) -> list[HubResult]:
        """
        Encontra nós com muitas conexões (potenciais pontos críticos).

        Query Cypher:
        MATCH (n)
        WITH n, size((n)<--()) as incoming, size((n)-->()) as outgoing
        WHERE incoming + outgoing >= $min
        RETURN n.name, labels(n), incoming, outgoing
        ORDER BY incoming + outgoing DESC
        """
        ...

    async def find_dead_code(self) -> list[str]:
        """
        Encontra nós sem dependentes (potencial código morto).

        Query Cypher:
        MATCH (n:Procedure)
        WHERE NOT (n)<--()
        AND n.layer <> 'ui'  // UI é entry point
        RETURN n.name
        """
        ...
```

## Configuration

### Settings

```python
# src/wxcode/config.py

class Settings(BaseSettings):
    # Existing...
    mongodb_uri: str = "mongodb://localhost:27017"

    # New Neo4j settings
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "wxcode"
```

### Environment Variables

```bash
# .env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=wxcode
```

## CLI Commands

### sync-neo4j

```bash
# Sincroniza projeto para Neo4j
wxcode sync-neo4j Linkpay_ADM

# Opções
--clear          # Limpa dados existentes antes de sincronizar
--validate       # Valida contagens após sync
--dry-run        # Mostra o que seria feito sem executar
```

### impact

```bash
# Análise de impacto
wxcode impact TABLE:CLIENTE
wxcode impact proc:ValidaCPF --depth 3

# Output:
# Impacto de TABLE:CLIENTE:
#   Depth 1: class:classCliente, proc:BuscaCliente
#   Depth 2: proc:CadastrarPedido, proc:EmitirNota
#   Depth 3: PAGE_Pedido, PAGE_Nota
# Total: 8 elementos afetados
```

### path

```bash
# Encontra caminhos entre dois nós
wxcode path PAGE_Login TABLE:USUARIO

# Output:
# Caminhos de PAGE_Login → TABLE:USUARIO:
#   1. PAGE_Login → proc:Autenticar → TABLE:USUARIO (2 hops)
#   2. PAGE_Login → class:classUsuario → TABLE:USUARIO (2 hops)
```

### hubs

```bash
# Encontra hubs (nós críticos)
wxcode hubs --min-connections 10

# Output:
# Hubs (≥10 conexões):
#   1. proc:RESTSend (45 incoming, 3 outgoing)
#   2. TABLE:CLIENTE (0 incoming, 28 outgoing)
#   3. class:classBasic (0 incoming, 12 outgoing)
```

## Cypher Query Examples

### Análise de Impacto

```cypher
// O que é afetado se eu mudar TABLE:CLIENTE?
MATCH path = (t:Table {name: 'CLIENTE'})<-[*1..5]-(affected)
RETURN DISTINCT affected.name, labels(affected)[0] as type,
       min(length(path)) as min_depth
ORDER BY min_depth, type
```

### Detecção de Ciclos

```cypher
// Encontra ciclos entre procedures
MATCH (p1:Procedure)-[:CALLS*2..10]->(p1)
RETURN DISTINCT p1.name as cycle_start
```

### Código Morto

```cypher
// Procedures nunca chamadas (exceto entry points)
MATCH (p:Procedure)
WHERE NOT ()-[:CALLS]->(p)
  AND NOT p.name STARTS WITH 'API'  // APIs são entry points
  AND NOT p.name STARTS WITH 'Task' // Tasks são entry points
RETURN p.name
ORDER BY p.name
```

### Comunidades

```cypher
// Procedures que frequentemente trabalham juntas
CALL gds.louvain.stream('wxcode-graph')
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).name AS name, communityId
ORDER BY communityId, name
```

## Testing Strategy

### Unit Tests

```python
# tests/test_neo4j_sync.py

@pytest.fixture
def neo4j_container():
    """Container Neo4j para testes."""
    # Usa testcontainers-python
    ...

async def test_sync_creates_all_nodes(neo4j_container, sample_project):
    """Verifica que sync cria todos os nós."""
    sync = Neo4jSyncService(neo4j_container)
    result = await sync.sync_project(sample_project.id)

    assert result.nodes_created == 493
    assert result.relationships_created == 1201

async def test_impact_returns_correct_depth(neo4j_container):
    """Verifica profundidade correta na análise de impacto."""
    analyzer = ImpactAnalyzer(neo4j_container)
    result = await analyzer.get_impact("TABLE:CLIENTE", max_depth=2)

    assert all(r.depth <= 2 for r in result.affected)
```

### Integration Tests

```python
# tests/test_neo4j_integration.py

async def test_full_sync_and_impact_analysis():
    """Teste E2E: sync + análise de impacto."""
    # 1. Sync projeto real
    await sync_service.sync_project(linkpay_project.id)

    # 2. Executa análise de impacto
    result = await analyzer.get_impact("TABLE:CLIENTE")

    # 3. Verifica que encontrou dependências conhecidas
    affected_names = [r.name for r in result.affected]
    assert "classCliente" in affected_names or any("Cliente" in n for n in affected_names)
```

## Performance Considerations

### Batch Operations

```python
# Usar UNWIND para batch inserts
CREATE_NODES_BATCH = """
UNWIND $nodes as node
CREATE (n:Procedure {
    name: node.name,
    layer: node.layer,
    mongo_id: node.mongo_id
})
"""

# Batch size recomendado: 1000-5000 nós por transação
```

### Indexes

```cypher
// Criar indexes para queries frequentes
CREATE INDEX node_name FOR (n:Table) ON (n.name);
CREATE INDEX node_name FOR (n:Class) ON (n.name);
CREATE INDEX node_name FOR (n:Procedure) ON (n.name);
CREATE INDEX node_name FOR (n:Page) ON (n.name);
CREATE INDEX node_layer FOR (n:Procedure) ON (n.layer);
```

### Connection Pooling

```python
# Usar driver com connection pooling
driver = GraphDatabase.driver(
    uri,
    auth=auth,
    max_connection_pool_size=50,
    connection_acquisition_timeout=60
)
```
