---
name: wx:status
description: Mostra status de conversão de um projeto.
allowed-tools: Bash
---

# wx:status - Status do Projeto

Mostra status detalhado de conversão de um projeto.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project` | string | Sim | Nome do projeto |
| `--show-skipped` | flag | Não | Mostrar elementos skipados |
| `--show-errors` | flag | Não | Mostrar erros de conversão |

## Uso

```bash
wxcode status <project> [options]
```

## Exemplos

```bash
# Status geral
wxcode status Linkpay_ADM

# Com skipados
wxcode status Linkpay_ADM --show-skipped

# Com erros
wxcode status Linkpay_ADM --show-errors
```

## Saída esperada

```
Project Status: Linkpay_ADM

Overview:
  Imported: 2024-01-15
  Last updated: 2024-01-20
  Target stack: FastAPI + Jinja2

Elements:
  Total: 150
  ├── Pages: 85
  ├── Procedures: 50
  ├── Classes: 10
  └── Schema: 5

Conversion Status:
  ████████░░░░░░░░░░░░ 40%

  Converted: 60
  Pending: 85
  Skipped: 3
  Errors: 2

Parsing Status:
  ✓ Enriched: 85 pages
  ✓ Procedures: 50 parsed
  ✓ Classes: 10 parsed
  ✓ Schema: parsed
  ✓ Dependencies: analyzed
```

## Próximos Passos

Baseado no status:
- Se pending > 0: `/wx:convert` para continuar
- Se errors > 0: `/wx:validate --show-errors`
- Se tudo convertido: `/wx:export`
