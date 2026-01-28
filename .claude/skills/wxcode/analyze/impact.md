---
name: wx:impact
description: Análise de impacto - o que muda se eu alterar elemento X?
allowed-tools: Bash
---

# wx:impact - Análise de Impacto

Mostra todos os elementos que seriam afetados por uma mudança.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `node_id` | string | Sim | Identificador do elemento |
| `--depth` | int | Não | Profundidade da análise (default: 2) |
| `--format` | string | Não | Formato: text, json, tree |

## Uso

```bash
wxcode impact <node_id> [--depth N] [--format FORMAT]
```

## Formatos de node_id

- `TABLE:CLIENTE` - Tabela do banco
- `proc:ValidaCPF` - Procedure
- `class:classUsuario` - Classe
- `PAGE_Login` - Página

## Exemplos

```bash
# Impacto de alterar tabela
wxcode impact TABLE:CLIENTE

# Impacto profundo de procedure
wxcode impact proc:ValidaCPF --depth 3

# Saída JSON para processamento
wxcode impact PAGE_Login --format json
```

## Saída esperada

```
Impact Analysis: TABLE:CLIENTE

Direct dependents (depth 1):
  - classCliente (uses table)
  - PROC_ListaClientes (queries table)
  - PAGE_CadCliente (displays data)

Indirect dependents (depth 2):
  - PAGE_PRINCIPAL (calls PROC_ListaClientes)
  - PAGE_Relatorio (uses classCliente)
  ...

Total affected: 12 elements
Risk level: HIGH (core entity)
```

## Interpretação

- **Depth 1**: Elementos que acessam diretamente
- **Depth 2+**: Elementos que dependem dos dependentes
- **Risk level**: Baseado na quantidade de dependentes

## Requer

Neo4j sincronizado. Execute `/wx:sync-neo4j` primeiro.
