# Tasks: fix-theme-assets

## Implementação

- [x] **Task 1:** Criar função `deploy_theme_assets()` em `src/wxcode/generator/theme_deployer.py`
  - Copiar CSS de `themes/<theme>/css/` para `<output>/app/static/css/`
  - Copiar JS de `themes/<theme>/js/` para `<output>/app/static/js/`
  - Copiar fonts de `themes/<theme>/fonts/` para `<output>/app/static/fonts/`
  - Copiar images de `themes/<theme>/images/` para `<output>/app/static/images/`
  - Retornar lista de arquivos copiados

- [x] **Task 2:** Adicionar comando `deploy-theme` no CLI
  ```bash
  wxcode deploy-theme <theme> -o <output>
  wxcode deploy-theme dashlite -o ./output/generated
  ```
  - Validar que tema existe
  - Chamar `deploy_theme_assets()`
  - Exibir resumo de arquivos copiados

- [x] **Task 3:** Adicionar flag `--deploy-assets` ao comando `convert-page`
  - Quando presente, chamar `deploy_theme_assets()` antes da conversão
  - Só executar se `--theme` também estiver presente

- [x] **Task 4:** Atualizar `themes list` para mostrar assets disponíveis
  - Listar quantidade de CSS, JS, fonts, images por tema

## Validação

- [x] **Task 5:** Teste manual end-to-end
  ```bash
  wxcode purge Linkpay_ADM
  wxcode import ./project-refs/Linkpay_ADM
  wxcode init-project Linkpay_ADM -o ./output/generated
  wxcode deploy-theme dashlite -o ./output/generated
  wxcode convert-page PAGE_Login --theme dashlite -o ./output/generated
  cd output/generated && uvicorn app.main:app --reload
  # Verificar que página carrega com estilo correto
  ```

- [x] **Task 6:** Adicionar testes unitários para `theme_deployer.py`
