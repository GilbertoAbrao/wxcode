# theme-deployer Specification

## Purpose
TBD - created by archiving change fix-theme-assets. Update Purpose after archive.
## Requirements
### Requirement: deploy-theme-command
O CLI MUST ter um comando `deploy-theme` que copia assets de um tema para o diretório static do projeto gerado.

#### Scenario: Deploy tema DashLite com sucesso
**Given** tema "dashlite" existe em `themes/dashlite-v3.3.0/`
**And** diretório de saída `./output/generated` existe
**When** usuário executa `wxcode deploy-theme dashlite -o ./output/generated`
**Then** arquivos CSS são copiados para `./output/generated/app/static/css/`
**And** arquivos JS são copiados para `./output/generated/app/static/js/`
**And** arquivos de fonts são copiados para `./output/generated/app/static/fonts/`
**And** arquivos de images são copiados para `./output/generated/app/static/images/`
**And** CLI exibe resumo com quantidade de arquivos copiados

#### Scenario: Tema não existe
**Given** tema "invalid-theme" não existe
**When** usuário executa `wxcode deploy-theme invalid-theme -o ./output/generated`
**Then** CLI exibe erro "Tema 'invalid-theme' não encontrado"
**And** comando retorna código de saída 1

### Requirement: deploy-assets-flag
O comando `convert-page` MUST ter flag `--deploy-assets` que automaticamente faz deploy do tema antes da conversão.

#### Scenario: Convert-page com deploy automático
**Given** tema "dashlite" existe
**And** projeto tem página PAGE_Login
**When** usuário executa `wxcode convert-page PAGE_Login --theme dashlite --deploy-assets -o ./output/generated`
**Then** assets do tema são copiados para static/
**And** página é convertida com referências corretas aos assets
**And** página renderiza com estilo do tema

#### Scenario: Deploy-assets sem theme
**Given** usuário não especificou `--theme`
**When** usuário executa `wxcode convert-page PAGE_Login --deploy-assets -o ./output/generated`
**Then** flag `--deploy-assets` é ignorada
**And** conversão prossegue normalmente sem assets de tema

### Requirement: themes-list-assets
O comando `themes list` MUST mostrar quantidade de assets disponíveis por tema.

#### Scenario: Listar temas com contagem de assets
**Given** tema "dashlite" tem 5 CSS, 10 JS, 3 fonts, 50 images
**When** usuário executa `wxcode themes list`
**Then** output inclui coluna "Assets" com formato "5 CSS, 10 JS, 3 fonts, 50 img"

