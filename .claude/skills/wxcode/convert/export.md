---
name: wx:export
description: Exporta projeto convertido para diretório final.
allowed-tools: Bash
---

# wx:export - Exportar Projeto

Exporta o projeto convertido para um diretório final, pronto para deploy.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project` | string | Sim | Nome do projeto |
| `-o, --output` | path | Sim | Diretório de destino |
| `--include-tests` | flag | Não | Incluir testes gerados |
| `--docker` | flag | Não | Incluir Dockerfile |

## Uso

```bash
wxcode export <project> -o <output> [options]
```

## Exemplos

```bash
# Exportar básico
wxcode export Linkpay_ADM -o ./dist/linkpay

# Com testes e Docker
wxcode export Linkpay_ADM -o ./dist/linkpay --include-tests --docker
```

## Estrutura Exportada

```
dist/linkpay/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── templates/
├── static/
├── tests/              (se --include-tests)
├── Dockerfile          (se --docker)
├── docker-compose.yml  (se --docker)
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Saída esperada

```
Exporting: Linkpay_ADM

Copying files...
  ✓ 150 Python files
  ✓ 85 templates
  ✓ Static assets

Generating configs...
  ✓ requirements.txt
  ✓ pyproject.toml
  ✓ README.md

Export complete: ./dist/linkpay

To run:
  cd ./dist/linkpay
  pip install -r requirements.txt
  uvicorn app.main:app --reload
```

## Próximos Passos

Após export:
- Testar: `cd output && uvicorn app.main:app`
- Deploy para servidor
- Configurar CI/CD
