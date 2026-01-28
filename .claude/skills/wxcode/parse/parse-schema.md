---
name: wx:parse-schema
description: Parseia schema do banco de dados de arquivos .wdd/.wda (Analysis).
allowed-tools: Bash
---

# wx:parse-schema - Parsear Schema

Parseia o arquivo de análise (.wdd/.wda) para extrair o modelo de dados.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project_dir` | path | Sim | Diretório do projeto WinDev |

## Uso

```bash
wxcode parse-schema <project_dir>
```

## Exemplos

```bash
# Parsear schema
wxcode parse-schema ./project-refs/Linkpay_ADM
```

## O que é extraído

- **Tabelas (Data Files)**: Nome, descrição
- **Campos (Items)**: Nome, tipo, tamanho, constraints
- **Chaves**: Primary, unique, foreign keys
- **Relacionamentos**: Links entre tabelas
- **Índices**: Índices compostos

## Mapeamento de Tipos

| WinDev | Python/Pydantic |
|--------|-----------------|
| Text | str |
| Integer | int |
| Real | float |
| Date | datetime.date |
| DateTime | datetime.datetime |
| Boolean | bool |
| Currency | Decimal |

## Saída esperada

```
Parsing schema in: Linkpay_ADM
Found Analysis: BD.wda
Tables: 45
  USUARIO: 12 fields, 2 keys
  CLIENTE: 25 fields, 3 keys
  BOLETO: 18 fields, 4 keys
...
Schema parsed successfully
```

## Próximos Passos

Após parsear schema:
- `/wx:analyze` - Analisar dependências
- `/wx:convert` - Converter (schema é a primeira camada)

## Collection Criada

- `schemas`: Modelo de dados completo do projeto
