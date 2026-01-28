---
name: wx:convert-page
description: Converte página específica usando LLM para conversão inteligente.
allowed-tools: Bash
---

# wx:convert-page - Converter Página com LLM

Converte uma página específica usando Claude para conversão inteligente.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `page_name` | string | Sim | Nome da página |
| `--project` | string | Não | Nome do projeto |
| `-o, --output` | path | Não | Diretório de saída |
| `--dry-run` | flag | Não | Apenas mostrar o que seria gerado |

## Uso

```bash
wxcode convert-page <page_name> [--project NAME] [-o DIR]
```

## Exemplos

```bash
# Converter página
wxcode convert-page PAGE_Login

# Especificar projeto e output
wxcode convert-page PAGE_Login --project Linkpay_ADM -o ./output

# Simular conversão
wxcode convert-page PAGE_Login --dry-run
```

## O que é gerado

Para cada página, são gerados:

1. **Route** (`routes/login.py`):
   - Endpoint FastAPI
   - Handlers de formulário
   - Validação de dados

2. **Template** (`templates/login.html`):
   - HTML Jinja2
   - Estrutura de controles
   - Bindings de dados

3. **Service** (se necessário):
   - Lógica de negócio extraída
   - Chamadas a procedures

## Saída esperada

```
Converting: PAGE_Login

Analyzing structure...
  Controls: 42
  Events: 8
  Local procedures: 5

Generating...
  ✓ routes/login.py (FastAPI route)
  ✓ templates/login.html (Jinja2)
  ✓ services/login_service.py (business logic)

LLM tokens used: 3500
```

## Diferença do /wx:convert

- `/wx:convert`: Conversão em batch, baseada em templates
- `/wx:convert-page`: Conversão individual, usa LLM para casos complexos

Use `/wx:convert-page` para:
- Páginas com lógica complexa
- Casos que precisam de revisão humana
- Debugging de conversão
