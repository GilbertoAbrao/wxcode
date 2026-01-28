---
name: wx:enrich
description: Enriquece elementos com controles, propriedades, eventos e procedures locais.
allowed-tools: Bash
---

# wx:enrich - Enriquecer Elementos

Parseia arquivos fonte (.wwh, .wdw) para extrair controles, eventos e procedures locais, e opcionalmente usa PDFs para propriedades visuais.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project_dir` | path | Sim | Diretório do projeto WinDev |
| `--pdf-docs` | path | Não | Diretório com PDFs divididos |
| `--batch-size` | int | Não | Tamanho do batch (default: 100) |

## Uso

```bash
wxcode enrich <project_dir> [--pdf-docs DIR] [--batch-size N]
```

## Exemplos

```bash
# Enriquecer sem PDFs
wxcode enrich ./project-refs/Linkpay_ADM

# Enriquecer com PDFs para propriedades visuais
wxcode enrich ./project-refs/Linkpay_ADM \
  --pdf-docs ./output/pdf_docs
```

## O que é extraído

- **Controles**: Hierarquia completa (parent/children)
- **Propriedades**: Posição, tamanho, visibilidade
- **Eventos**: OnClick, OnChange, OnOpen, etc.
- **Procedures locais**: Código dentro da página
- **Dependências**: Referências a outros elementos

## Saída esperada

```
Enriching project: Linkpay_ADM
Processing PAGE_Login.wwh...
  Found 42 controls
  Found 8 events with code
  Found 5 local procedures
Processing PAGE_PRINCIPAL.wwh...
...
Enriched 85 pages
Total controls: 3500
Total events: 450
```

## Próximos Passos

Após enriquecer:
- `/wx:parse-procedures` - Parsear procedures globais
- `/wx:analyze` - Analisar dependências
- `/page-tree PAGE_Login` - Visualizar estrutura de uma página

## Collections Atualizadas

- `elements`: Adiciona `controls_count`, `ast.events`, `ast.procedures`
- `controls`: Novos documentos para cada controle
- `control_types`: Tipos de controles encontrados
