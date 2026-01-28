---
name: wx:list-orphans
description: Lista controles órfãos (sem parent identificado) de um projeto.
allowed-tools: Bash
---

# wx:list-orphans - Listar Controles Órfãos

Lista controles que não têm parent identificado na hierarquia.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project` | string | Sim | Nome do projeto |
| `--page` | string | Não | Filtrar por página específica |
| `--type` | int | Não | Filtrar por type_code |

## Uso

```bash
wxcode list-orphans <project> [--page PAGE] [--type CODE]
```

## Exemplos

```bash
# Listar todos os órfãos
wxcode list-orphans Linkpay_ADM

# Filtrar por página
wxcode list-orphans Linkpay_ADM --page PAGE_Login

# Filtrar por tipo (ex: 8 = Image)
wxcode list-orphans Linkpay_ADM --type 8
```

## O que são órfãos

Controles são marcados como órfãos quando:
- Não têm `parent_control_id` definido
- Parent referenciado não existe
- Hierarquia não pode ser reconstruída

## Saída esperada

```
Orphan controls in Linkpay_ADM:

PAGE_Login:
  - EDT_NoName1 (type: 2, Edit)
  - IMG_Background (type: 8, Image)

PAGE_PRINCIPAL:
  - STC_Version (type: 3, Static)
...

Total orphans: 45 (1.3% of 3500 controls)
```

## Próximos Passos

Órfãos podem indicar:
- Problema no parsing - verificar arquivo fonte
- Controles dinâmicos - criados em runtime
- Templates - controles herdados

Use `/page-tree PAGE_Name` para investigar a estrutura.
