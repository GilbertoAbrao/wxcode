---
name: wx:deploy-theme
description: Aplica tema ao projeto convertido.
allowed-tools: Bash
---

# wx:deploy-theme - Deploy de Tema

Aplica um tema ao projeto FastAPI + Jinja2 gerado.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `theme` | string | Sim | Nome do tema |
| `--output` | path | Não | Diretório do projeto |
| `--force` | flag | Não | Sobrescrever arquivos existentes |

## Uso

```bash
wxcode deploy-theme <theme> [--output DIR] [--force]
```

## Exemplos

```bash
# Deploy tema padrão
wxcode deploy-theme dashlite

# Para projeto específico
wxcode deploy-theme dashlite --output ./output/linkpay

# Forçar sobrescrita
wxcode deploy-theme bootstrap --output ./output/linkpay --force
```

## O que é copiado

1. **Static assets**:
   - CSS do tema
   - JavaScript
   - Fonts
   - Images

2. **Templates base**:
   - `base.html` (layout)
   - `_partials/` (componentes)

3. **Configuração**:
   - Variáveis de tema
   - Paths de assets

## Saída esperada

```
Deploying theme: dashlite

Copying assets...
  ✓ static/css/dashlite.css
  ✓ static/js/dashlite.js
  ✓ static/fonts/ (12 files)

Copying templates...
  ✓ templates/base.html
  ✓ templates/_partials/navbar.html
  ✓ templates/_partials/sidebar.html
  ...

Updating config...
  ✓ app/config.py (theme settings)

Deploy complete!

Theme applied to: ./output/linkpay
```

## Componentes do Tema

Após deploy, use a documentação do tema:
- `.claude/skills/themes/dashlite/` - Componentes disponíveis
- Cada componente tem exemplos de uso

## Trocar Tema

Para trocar tema, use `--force`:
```bash
wxcode deploy-theme bootstrap --force
```
