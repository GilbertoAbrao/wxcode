---
name: wx:analyze
description: Analisa dependências do projeto e constrói grafo.
allowed-tools: Bash
---

# wx:analyze - Analisar Dependências

Constrói grafo de dependências entre elementos do projeto.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project` | string | Sim | Nome do projeto |
| `--export-dot` | path | Não | Exportar grafo em formato DOT |
| `--detect-cycles` | flag | Não | Detectar e reportar ciclos |

## Uso

```bash
wxcode analyze <project> [--export-dot FILE] [--detect-cycles]
```

## Exemplos

```bash
# Análise básica
wxcode analyze Linkpay_ADM

# Exportar grafo para visualização
wxcode analyze Linkpay_ADM --export-dot ./output/deps.dot

# Detectar ciclos
wxcode analyze Linkpay_ADM --detect-cycles
```

## O que é analisado

- **Chamadas de procedures**: PAGE_A → ServerProcedures
- **Uso de classes**: PAGE_B → classUsuario
- **Acesso a dados**: PROC_X → TABLE:CLIENTE
- **Includes**: Template → PAGE_Base

## Saída esperada

```
Analyzing dependencies: Linkpay_ADM

Building graph...
  Nodes: 250
  Edges: 1200

Layers detected:
  UI: 85 pages
  Business: 50 procedure groups
  Domain: 25 classes
  Schema: 45 tables

Cycles found: 3
  - PAGE_A → PROC_B → PAGE_A
  ...

Topological order computed.
```

## Próximos Passos

Após análise:
- `/wx:sync-neo4j` - Visualizar no Neo4j
- `/wx:plan` - Planejar conversão
- `/wx:impact TABLE:X` - Análise de impacto
