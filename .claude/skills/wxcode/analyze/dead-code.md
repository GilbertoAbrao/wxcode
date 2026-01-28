---
name: wx:dead-code
description: Detecta código potencialmente não utilizado.
allowed-tools: Bash
---

# wx:dead-code - Detectar Código Morto

Encontra elementos que não são referenciados por nenhum outro.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `--project` | string | Não | Filtrar por projeto |
| `--type` | string | Não | Filtrar por tipo: page, proc, class |
| `--exclude-entry-points` | flag | Não | Excluir páginas de entrada |

## Uso

```bash
wxcode dead-code [--project NAME] [--type TYPE] [--exclude-entry-points]
```

## Exemplos

```bash
# Detectar todo código morto
wxcode dead-code

# Apenas procedures não utilizadas
wxcode dead-code --type proc

# Excluir páginas de entrada (podem ser acessadas diretamente)
wxcode dead-code --exclude-entry-points
```

## O que é detectado

- **Procedures não chamadas**: Nenhuma referência encontrada
- **Classes não instanciadas**: Nenhum `new` ou uso
- **Páginas isoladas**: Sem navegação de/para

## Saída esperada

```
Dead Code Analysis

Potentially unused procedures:
  - PROC_Deprecated (last modified: 2022-01-15)
  - PROC_TestOnly (name suggests test)
  - PROC_OldValidation

Potentially unused classes:
  - classLegacy
  - classBackup

Orphan pages (no navigation to):
  - PAGE_Debug
  - PAGE_Admin_Old

Summary:
  - 5 procedures
  - 2 classes
  - 2 pages

Recommendation: Review before deleting
```

## Falsos Positivos

Podem não ser realmente mortos:
- Chamados via reflexão/dinâmico
- Entry points (páginas acessadas por URL)
- Usados em queries SQL
- Referenciados em configurações

## Requer

Neo4j sincronizado. Execute `/wx:sync-neo4j` primeiro.
