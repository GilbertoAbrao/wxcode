---
name: wx:init-project
description: Inicializa estrutura de projeto FastAPI a partir da conversão.
allowed-tools: Bash
---

# wx:init-project - Inicializar Projeto FastAPI

Cria a estrutura base de um projeto FastAPI + Jinja2 a partir dos elementos convertidos.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `output_dir` | path | Sim | Diretório de saída para o projeto |
| `--project` | string | Não | Nome do projeto no MongoDB |
| `--theme` | string | Não | Tema a aplicar (default: dashlite) |

## Uso

```bash
wxcode init-project <output_dir> [--project NAME] [--theme THEME]
```

## Exemplos

```bash
# Inicializar projeto no diretório output
wxcode init-project ./output/linkpay

# Especificar projeto e tema
wxcode init-project ./output/app --project Linkpay_ADM --theme dashlite
```

## Estrutura Criada

```
output/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configurações
│   ├── models/              # Pydantic models
│   ├── routes/              # Rotas FastAPI
│   ├── services/            # Business logic
│   └── templates/           # Jinja2 templates
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── requirements.txt
└── pyproject.toml
```

## Próximos Passos

Após inicializar:
- `/wx:convert` - Converter elementos para o projeto
- `/wx:deploy-theme` - Aplicar tema (se não especificado)
- `/wx:test-app` - Testar a aplicação

## Notas

- O comando cria apenas a estrutura base
- Elementos convertidos são adicionados via `/wx:convert`
- Temas podem ser trocados depois com `/wx:deploy-theme`
