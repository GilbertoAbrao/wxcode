---
name: wx:check-duplicates
description: Verifica elementos duplicados no MongoDB.
allowed-tools: Bash
---

# wx:check-duplicates - Verificar Duplicatas

Detecta elementos duplicados no MongoDB.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `--project` | string | Não | Filtrar por projeto |
| `--fix` | flag | Não | Remover duplicatas automaticamente |

## Uso

```bash
wxcode check-duplicates [--project NAME] [--fix]
```

## Exemplos

```bash
# Verificar todos os projetos
wxcode check-duplicates

# Verificar projeto específico
wxcode check-duplicates --project Linkpay_ADM

# Corrigir automaticamente
wxcode check-duplicates --fix
```

## O que é verificado

- **Elementos**: Mesmo `source_name` no mesmo projeto
- **Controles**: Mesmo `name` na mesma página
- **Procedures**: Mesmo nome no mesmo grupo

## Saída esperada

```
Checking for duplicates...

Found 3 duplicate elements:

  PAGE_Login (Linkpay_ADM):
    - _id: 65a1b2c3... (created: 2024-01-15)
    - _id: 65a4d5e6... (created: 2024-01-16) [DUPLICATE]

  PROC_Util (Linkpay_ADM):
    - _id: 65a7f8g9... (created: 2024-01-15)
    - _id: 65b0a1b2... (created: 2024-01-17) [DUPLICATE]

Recommendation:
  Run with --fix to remove duplicates (keeps oldest)
```

## Causas comuns

- Re-importação sem purge
- Importação parcial interrompida
- Múltiplas importações do mesmo projeto
