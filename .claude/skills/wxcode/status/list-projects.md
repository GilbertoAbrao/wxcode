---
name: wx:list-projects
description: Lista todos os projetos no MongoDB.
allowed-tools: Bash
---

# wx:list-projects - Listar Projetos

Lista todos os projetos WinDev/WebDev importados no MongoDB.

## Parâmetros

Nenhum parâmetro obrigatório.

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `--format` | string | Não | Formato: table, json (default: table) |

## Uso

```bash
wxcode list-projects [--format FORMAT]
```

## Exemplos

```bash
# Listar projetos
wxcode list-projects

# Formato JSON
wxcode list-projects --format json
```

## Saída esperada

```
Projects in MongoDB:

  Name              Elements  Controls  Status      Imported
  ────────────────────────────────────────────────────────────
  Linkpay_ADM       150       3500      enriched    2024-01-15
  Projeto_Teste     45        800       imported    2024-01-10
  Legacy_System     200       5000      converted   2024-01-05

Total: 3 projects
```

## Próximos Passos

Para cada projeto:
- `/wx:status <project>` - Ver status detalhado
- `/wx:list-elements <project>` - Listar elementos
- `/wx:analyze <project>` - Analisar dependências
