---
name: wx:test-app
description: Inicia servidor de teste para aplicação gerada.
allowed-tools: Bash
---

# wx:test-app - Testar Aplicação

Inicia um servidor de desenvolvimento para testar a aplicação convertida.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `app_path` | path | Sim | Caminho da aplicação |
| `--port` | int | Não | Porta do servidor (default: 8000) |
| `--reload` | flag | Não | Auto-reload em mudanças |

## Uso

```bash
wxcode test-app <app_path> [--port PORT] [--reload]
```

## Exemplos

```bash
# Iniciar servidor
wxcode test-app ./output/linkpay

# Porta customizada
wxcode test-app ./output/linkpay --port 3000

# Com auto-reload
wxcode test-app ./output/linkpay --reload
```

## Pré-requisitos

Antes de testar:
1. Dependências instaladas: `pip install -r requirements.txt`
2. MongoDB rodando (para dados)
3. Variáveis de ambiente configuradas

## Saída esperada

```
Starting test server...

App path: ./output/linkpay
Port: 8000
Reload: enabled

Installing dependencies...
  ✓ fastapi
  ✓ uvicorn
  ✓ jinja2
  ...

Starting uvicorn...
  INFO:     Uvicorn running on http://127.0.0.1:8000
  INFO:     Started reloader process

Server running at: http://localhost:8000

Press Ctrl+C to stop
```

## Endpoints úteis

- `http://localhost:8000/` - Página inicial
- `http://localhost:8000/docs` - Swagger UI
- `http://localhost:8000/redoc` - ReDoc

## Troubleshooting

| Erro | Solução |
|------|---------|
| Port in use | Usar `--port` diferente |
| Module not found | Verificar requirements.txt |
| Template not found | Verificar estrutura de pastas |
