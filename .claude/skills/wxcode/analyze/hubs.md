---
name: wx:hubs
description: Encontra nós críticos com muitas conexões (hubs).
allowed-tools: Bash
---

# wx:hubs - Encontrar Hubs

Lista elementos com mais conexões (dependências) no grafo.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `--min-connections` | int | Não | Mínimo de conexões (default: 10) |
| `--type` | string | Não | Filtrar por tipo: page, proc, class, table |
| `--direction` | string | Não | in, out, both (default: both) |

## Uso

```bash
wxcode hubs [--min-connections N] [--type TYPE] [--direction DIR]
```

## Exemplos

```bash
# Hubs com 10+ conexões
wxcode hubs

# Hubs com 20+ conexões
wxcode hubs --min-connections 20

# Apenas procedures
wxcode hubs --type proc

# Elementos mais dependidos (incoming)
wxcode hubs --direction in
```

## Saída esperada

```
Hub Analysis (min: 10 connections)

Top Hubs:
  1. ServerProcedures (proc)
     - Incoming: 45
     - Outgoing: 12
     - Total: 57

  2. TABLE:USUARIO (table)
     - Incoming: 38
     - Outgoing: 0
     - Total: 38

  3. classBase (class)
     - Incoming: 25
     - Outgoing: 5
     - Total: 30
...

Found 15 hubs
```

## Interpretação

- **Alto incoming**: Muito dependido, mudanças têm grande impacto
- **Alto outgoing**: Depende de muitos, vulnerável a mudanças externas
- **Hubs**: Candidatos a refactoring, testes prioritários

## Requer

Neo4j sincronizado. Execute `/wx:sync-neo4j` primeiro.
