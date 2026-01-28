---
name: wx:path
description: Encontra caminhos entre dois elementos no grafo.
allowed-tools: Bash
---

# wx:path - Encontrar Caminhos

Encontra todos os caminhos de dependência entre dois elementos.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `source` | string | Sim | Elemento de origem |
| `target` | string | Sim | Elemento de destino |
| `--max-depth` | int | Não | Profundidade máxima (default: 5) |

## Uso

```bash
wxcode path <source> <target> [--max-depth N]
```

## Exemplos

```bash
# Caminho entre página e tabela
wxcode path PAGE_Login TABLE:USUARIO

# Limitar profundidade
wxcode path PAGE_A PAGE_B --max-depth 3
```

## Saída esperada

```
Paths from PAGE_Login to TABLE:USUARIO:

Path 1 (length: 2):
  PAGE_Login
    → PROC_Autenticar
    → TABLE:USUARIO

Path 2 (length: 3):
  PAGE_Login
    → classUsuario
    → classUsuario.Buscar()
    → TABLE:USUARIO

Found 2 paths
Shortest: 2 hops
```

## Casos de Uso

- **Entender dependências**: Como PAGE_A chega em TABLE_X?
- **Debugging**: Por que mudança em X afetou Y?
- **Refactoring**: Qual o impacto de mover procedure?

## Requer

Neo4j sincronizado. Execute `/wx:sync-neo4j` primeiro.
