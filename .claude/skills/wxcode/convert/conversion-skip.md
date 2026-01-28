---
name: wx:conversion-skip
description: Marca elemento para ser ignorado na conversão.
allowed-tools: Bash
---

# wx:conversion-skip - Marcar Skip

Marca um elemento para ser ignorado na conversão.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project_name` | string | Sim | Nome do projeto |
| `element_name` | string | Sim | Nome do elemento |
| `--reason` | string | Não | Motivo do skip |
| `--unskip` | flag | Não | Remover marcação de skip |

## Uso

```bash
wxcode conversion-skip <project> <element> [--reason TEXT] [--unskip]
```

## Exemplos

```bash
# Marcar para skip
wxcode conversion-skip Linkpay_ADM PAGE_Debug --reason "Página de debug, não converter"

# Marcar múltiplos
wxcode conversion-skip Linkpay_ADM PAGE_Test
wxcode conversion-skip Linkpay_ADM PROC_Deprecated

# Remover skip
wxcode conversion-skip Linkpay_ADM PAGE_Debug --unskip
```

## Quando usar skip

- **Páginas de debug/teste**: Não necessárias em produção
- **Código legado**: Será reescrito manualmente
- **Elementos parciais**: Conversão manual planejada
- **Dependências externas**: Requerem tratamento especial

## Saída esperada

```
Marking skip: PAGE_Debug

Element: PAGE_Debug
Status: skip
Reason: Página de debug, não converter

Updated successfully.
```

## Verificar elementos skipados

Use `/wx:status` para ver todos os elementos marcados:

```bash
wxcode status Linkpay_ADM --show-skipped
```
