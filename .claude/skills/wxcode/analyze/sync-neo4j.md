---
name: wx:sync-neo4j
description: Sincroniza grafo de dependências para Neo4j.
allowed-tools: Bash
---

# wx:sync-neo4j - Sincronizar com Neo4j

Exporta o grafo de dependências do MongoDB para Neo4j para visualização e queries avançadas.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project` | string | Sim | Nome do projeto |
| `--dry-run` | flag | Não | Simular sem alterar Neo4j |
| `--no-clear` | flag | Não | Não limpar dados anteriores |

## Uso

```bash
wxcode sync-neo4j <project> [--dry-run] [--no-clear]
```

## Exemplos

```bash
# Sincronizar projeto
wxcode sync-neo4j Linkpay_ADM

# Simular primeiro
wxcode sync-neo4j Linkpay_ADM --dry-run

# Adicionar sem limpar (merge)
wxcode sync-neo4j Linkpay_ADM --no-clear
```

## Modelo Neo4j

Nodes:
- `(:Page {name, layer, topological_order})`
- `(:Procedure {name, layer})`
- `(:Class {name, layer})`
- `(:Table {name, layer})`

Relationships:
- `(:Page)-[:CALLS]->(:Procedure)`
- `(:Page)-[:USES]->(:Class)`
- `(:Procedure)-[:ACCESSES]->(:Table)`

## Saída esperada

```
Syncing to Neo4j: Linkpay_ADM

Clearing existing data...
Creating nodes: 250
Creating relationships: 1200

Sync complete!
Neo4j Browser: http://localhost:7474
```

## Próximos Passos

No Neo4j Browser, experimente:
```cypher
// Ver todo o grafo
MATCH (n) RETURN n LIMIT 100

// Páginas que usam mais procedures
MATCH (p:Page)-[:CALLS]->(proc)
RETURN p.name, count(proc) as calls
ORDER BY calls DESC
```

Ou use as skills:
- `/wx:impact` - Análise de impacto
- `/wx:path` - Encontrar caminhos
- `/wx:hubs` - Nós críticos
