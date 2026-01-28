---
name: wx:convert
description: Converte elementos WinDev para FastAPI + Jinja2.
allowed-tools: Bash
---

# wx:convert - Converter Elementos

Converte elementos do projeto WinDev para FastAPI + Jinja2.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project` | string | Sim | Nome do projeto |
| `-o, --output` | path | Sim | Diretório de saída |
| `-e, --element` | string | Não | Elemento específico |
| `--layer` | string | Não | Camada: schema, domain, service, route, template |
| `--force` | flag | Não | Sobrescrever existentes |

## Uso

```bash
wxcode convert <project> -o <output> [options]
```

## Exemplos

```bash
# Converter todo o projeto
wxcode convert Linkpay_ADM -o ./output/generated

# Converter elemento específico
wxcode convert Linkpay_ADM -e PAGE_Login -o ./output/generated

# Converter por camada
wxcode convert Linkpay_ADM --layer schema -o ./output/generated
wxcode convert Linkpay_ADM --layer domain -o ./output/generated
```

## Camadas de Conversão

| Camada | Entrada | Saída |
|--------|---------|-------|
| schema | .wdd | `models/*.py` (Pydantic) |
| domain | .wdc | `domain/*.py` (classes) |
| service | .wdg | `services/*.py` |
| route | .wwh | `routes/*.py` (FastAPI) |
| template | .wwh | `templates/*.html` (Jinja2) |

## Saída esperada

```
Converting: Linkpay_ADM

Layer: schema
  ✓ USUARIO → models/usuario.py
  ✓ CLIENTE → models/cliente.py
  ...

Layer: route
  ✓ PAGE_Login → routes/login.py
  ✓ PAGE_PRINCIPAL → routes/principal.py
  ...

Converted: 150 elements
Skipped: 5 (marked skip)
Errors: 2 (see errors.log)
```

## Próximos Passos

Após conversão:
- `/wx:validate` - Validar código gerado
- `/wx:test-app` - Testar aplicação
- `/wx:export` - Exportar projeto final
