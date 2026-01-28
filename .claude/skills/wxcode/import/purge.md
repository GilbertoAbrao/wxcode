---
name: wx:purge
description: Remove projeto e todos seus dados do MongoDB. IRREVERSÍVEL.
allowed-tools: Bash
---

# wx:purge - Remover Projeto

Remove um projeto e todos os dados associados do MongoDB.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project_name` | string | Sim | Nome do projeto a remover |
| `--force` | flag | Não | Não pedir confirmação |

## Uso

```bash
wxcode purge <project_name> [--force]
```

## Exemplos

```bash
# Remover com confirmação
wxcode purge Linkpay_ADM

# Remover sem confirmação (cuidado!)
wxcode purge Linkpay_ADM --force
```

## O que é removido

- Registro do projeto (collection `projects`)
- Todos os elementos (collection `elements`)
- Todos os controles (collection `controls`)
- Todas as procedures (collection `procedures`)
- Schema parseado (collection `schemas`)

## Saída esperada

```
Are you sure you want to purge project 'Linkpay_ADM'? [y/N]: y
Deleting 150 elements...
Deleting 3500 controls...
Deleting 80 procedures...
Deleting project record...
Project 'Linkpay_ADM' purged successfully.
```

## Próximos Passos

Após purge, você pode:
- `/wx:import` - Reimportar o projeto
- `/wx:list-projects` - Verificar projetos restantes

## Notas

- Esta operação é IRREVERSÍVEL
- Não afeta arquivos no disco (apenas MongoDB)
- Use com cautela em produção
