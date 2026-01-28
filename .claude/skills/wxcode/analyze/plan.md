---
name: wx:plan
description: Planeja ordem de conversão baseado em dependências.
allowed-tools: Bash
---

# wx:plan - Planejar Conversão

Gera plano de conversão com ordem topológica respeitando dependências.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project` | string | Sim | Nome do projeto |
| `--output` | path | Não | Salvar plano em arquivo |
| `--format` | string | Não | Formato: text, json, markdown |

## Uso

```bash
wxcode plan <project> [--output FILE] [--format FORMAT]
```

## Exemplos

```bash
# Ver plano no terminal
wxcode plan Linkpay_ADM

# Salvar como markdown
wxcode plan Linkpay_ADM --output ./plan.md --format markdown
```

## Ordem de Conversão

A conversão segue ordem topológica por camadas:

1. **Schema** (.wdd → Pydantic models)
2. **Domain** (.wdc → Python classes)
3. **Service** (.wdg → Services)
4. **Route** (.wwh → FastAPI routes)
5. **Template** (.wwh → Jinja2)

## Saída esperada

```
Conversion Plan: Linkpay_ADM

Phase 1 - Schema (45 items):
  1. TABLE:USUARIO
  2. TABLE:CLIENTE
  ...

Phase 2 - Domain (25 items):
  1. classBase
  2. classUsuario (depends: classBase)
  ...

Phase 3 - Service (50 items):
  1. ServerProcedures
  2. UtilProcedures
  ...

Phase 4-5 - UI (85 items):
  1. PAGE_Login
  2. PAGE_PRINCIPAL
  ...

Estimated: 205 elements
```

## Próximos Passos

Com o plano:
- `/wx:convert` - Executar conversão
- `/wx:convert Linkpay_ADM --layer schema` - Converter por camada
