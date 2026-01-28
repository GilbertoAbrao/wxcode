---
name: wx:list-elements
description: Lista elementos de um projeto com filtros.
allowed-tools: Bash
---

# wx:list-elements - Listar Elementos

Lista elementos de um projeto com filtros opcionais.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project_name` | string | Sim | Nome do projeto |
| `--type` | string | Não | Filtrar por tipo: page, proc, class, query |
| `--status` | string | Não | Filtrar por status: pending, converted, skip |
| `--layer` | string | Não | Filtrar por camada: ui, business, domain, schema |
| `--limit` | int | Não | Limitar quantidade |

## Uso

```bash
wxcode list-elements <project> [options]
```

## Exemplos

```bash
# Listar todos
wxcode list-elements Linkpay_ADM

# Apenas páginas
wxcode list-elements Linkpay_ADM --type page

# Elementos não convertidos
wxcode list-elements Linkpay_ADM --status pending

# Por camada
wxcode list-elements Linkpay_ADM --layer ui --limit 20
```

## Saída esperada

```
Elements in Linkpay_ADM:

Type      Name                  Layer     Status     Controls
─────────────────────────────────────────────────────────────
page      PAGE_Login            ui        converted  42
page      PAGE_PRINCIPAL        ui        pending    85
page      PAGE_CadCliente       ui        pending    120
proc      ServerProcedures      business  converted  -
class     classUsuario          domain    pending    -
...

Showing 20 of 150 elements
```

## Próximos Passos

Para um elemento específico:
- `/page-tree <element>` - Ver estrutura da página
- `/wx:convert ... -e <element>` - Converter elemento
- `/wx:conversion-skip` - Marcar skip
