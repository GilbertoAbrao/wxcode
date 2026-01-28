---
name: wx:validate
description: Valida código convertido (syntax, imports, types).
allowed-tools: Bash
---

# wx:validate - Validar Conversão

Valida o código Python gerado pela conversão.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project` | string | Sim | Nome do projeto |
| `--output` | path | Não | Diretório do código gerado |
| `--fix` | flag | Não | Tentar corrigir erros automaticamente |

## Uso

```bash
wxcode validate <project> [--output DIR] [--fix]
```

## Exemplos

```bash
# Validar projeto
wxcode validate Linkpay_ADM

# Validar diretório específico
wxcode validate Linkpay_ADM --output ./output/generated

# Tentar correções automáticas
wxcode validate Linkpay_ADM --fix
```

## O que é validado

1. **Syntax**: Código Python válido
2. **Imports**: Módulos existem e são importáveis
3. **Types**: Type hints consistentes
4. **Templates**: Jinja2 válido
5. **Routes**: Endpoints corretos

## Saída esperada

```
Validating: Linkpay_ADM

Checking syntax...
  ✓ 150 files OK
  ✗ 2 files with errors

Checking imports...
  ✓ All imports resolved

Checking types...
  ⚠ 5 type warnings

Errors:
  routes/cliente.py:45: SyntaxError: unexpected indent
  services/boleto.py:12: NameError: 'classX' not defined

Warnings:
  models/usuario.py:10: Missing return type
  ...

Summary: 2 errors, 5 warnings
```

## Próximos Passos

Após validação:
- Corrigir erros manualmente ou com `--fix`
- `/wx:test-app` - Testar a aplicação
- `/wx:export` - Exportar quando válido
