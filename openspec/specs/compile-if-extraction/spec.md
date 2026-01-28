# compile-if-extraction Specification

## Purpose
TBD - created by archiving change add-compile-if-extraction. Update Purpose after archive.
## Requirements
### Requirement: Parse COMPILE IF blocks

O sistema MUST detectar e parsear blocos `<COMPILE IF Configuration="...">` em código WLanguage.

#### Scenario: Simple COMPILE IF block

- **GIVEN** código WLanguage contendo:
  ```wlanguage
  <COMPILE IF Configuration="Producao">
      CONSTANT URL_API = "https://api.linkpay.com.br"
  <END>
  ```
- **WHEN** `CompileIfExtractor.extract(code)` é chamado
- **THEN** deve retornar um `CompileIfBlock` com:
  - `conditions: ["Producao"]`
  - `operator: None`
  - `code` contendo a linha do CONSTANT

#### Scenario: COMPILE IF with OR operator

- **GIVEN** código WLanguage contendo:
  ```wlanguage
  <COMPILE IF Configuration="Homolog" OR Configuration="API_Homolog">
      gParams.URL = "https://hml.api.com"
  <END>
  ```
- **WHEN** `CompileIfExtractor.extract(code)` é chamado
- **THEN** deve retornar um `CompileIfBlock` com:
  - `conditions: ["Homolog", "API_Homolog"]`
  - `operator: "OR"`

#### Scenario: Multiple COMPILE IF blocks

- **GIVEN** código com 3 blocos COMPILE IF para configs diferentes
- **WHEN** `CompileIfExtractor.extract(code)` é chamado
- **THEN** deve retornar lista com 3 `CompileIfBlock`

#### Scenario: Commented COMPILE IF

- **GIVEN** código com `//<COMPILE IF ...>` (comentado)
- **WHEN** `CompileIfExtractor.extract(code)` é chamado
- **THEN** deve ignorar o bloco comentado

---

### Requirement: Extract configuration variables

O sistema MUST extrair variáveis e constantes definidas dentro de blocos COMPILE IF.

#### Scenario: Extract CONSTANT

- **GIVEN** bloco COMPILE IF contendo `CONSTANT URL_API = "https://..."`
- **WHEN** variáveis são extraídas
- **THEN** deve retornar `ExtractedVariable` com:
  - `name: "URL_API"`
  - `value: "https://..."`
  - `var_type: "CONSTANT"`

#### Scenario: Extract global variable assignment

- **GIVEN** bloco COMPILE IF contendo `gParams.URL = "https://..."`
- **WHEN** variáveis são extraídas
- **THEN** deve retornar `ExtractedVariable` com:
  - `name: "GPARAMS_URL"` (normalizado)
  - `value: "https://..."`
  - `var_type: "GLOBAL"`

#### Scenario: Extract multiple variables from same block

- **GIVEN** bloco COMPILE IF com 3 atribuições
- **WHEN** variáveis são extraídas
- **THEN** deve retornar 3 `ExtractedVariable`

---

### Requirement: Build ConfigurationContext

O sistema MUST construir um `ConfigurationContext` a partir dos blocos extraídos.

#### Scenario: Group variables by configuration

- **GIVEN** blocos extraídos com variáveis para Producao e Homolog
- **WHEN** `ConfigurationContext.from_blocks(blocks)` é chamado
- **THEN** deve ter `variables_by_config` com chaves "Producao" e "Homolog"

#### Scenario: Same variable in multiple configs

- **GIVEN** `URL_API` definido em Producao e Homolog com valores diferentes
- **WHEN** context é construído
- **THEN** cada config deve ter seu próprio valor para `URL_API`

#### Scenario: Variable in OR condition

- **GIVEN** variável em bloco `Configuration="A" OR Configuration="B"`
- **WHEN** context é construído
- **THEN** variável deve aparecer em AMBAS as configs "A" e "B" com mesmo valor

---

### Requirement: Generate Python configuration files

O sistema MUST gerar arquivos de configuração para stack Python/FastAPI.

#### Scenario: Generate settings.py

- **GIVEN** `ConfigurationContext` com variáveis `URL_API` e `CLIENT_ID`
- **WHEN** `PythonConfigGenerator.generate(context, output_dir)` é chamado
- **THEN** deve gerar `config/settings.py` com:
  - Classe `Settings` herdando de `BaseSettings`
  - Atributos `URL_API: str` e `CLIENT_ID: str`
  - Função `get_settings()`

#### Scenario: Generate .env.example

- **GIVEN** `ConfigurationContext` com variáveis
- **WHEN** gerador é executado
- **THEN** deve gerar `.env.example` com todas as variáveis e valores default

#### Scenario: Generate .env with config values

- **GIVEN** conversão para configuration "Producao"
- **WHEN** gerador é executado
- **THEN** deve gerar `.env` com valores específicos de Producao

---

### Requirement: CLI convert by configuration

O sistema MUST permitir conversão por configuration específica via CLI.

#### Scenario: Convert specific configuration

- **GIVEN** projeto "Linkpay_ADM" com configurations Producao e Homolog
- **WHEN** executamos `wxcode convert Linkpay_ADM --config Producao`
- **THEN** deve gerar arquivos em `./output/Producao/`
- **AND** deve usar valores de Producao nos arquivos de config

#### Scenario: Convert all configurations

- **GIVEN** projeto com 4 configurations
- **WHEN** executamos `wxcode convert Linkpay_ADM --all-configs`
- **THEN** deve gerar 4 pastas: `./output/{config_name}/` para cada uma

#### Scenario: Custom output base

- **GIVEN** projeto com configuration Producao
- **WHEN** executamos `wxcode convert Linkpay_ADM --config Producao --output ./deploy`
- **THEN** deve gerar arquivos em `./deploy/Producao/`

#### Scenario: Configuration not found

- **GIVEN** projeto sem configuration "InvalidConfig"
- **WHEN** executamos `wxcode convert Linkpay_ADM --config InvalidConfig`
- **THEN** deve exibir erro claro: "Configuration 'InvalidConfig' não encontrada"

---

### Requirement: Filter elements by configuration

O sistema MUST filtrar elementos baseado no campo `excluded_from` durante a conversão.

#### Scenario: Exclude element from configuration

- **GIVEN** elemento PAGE_Login com `excluded_from: ["13051986534836779703"]`
- **AND** configuration API_Homolog com `configuration_id: "13051986534836779703"`
- **WHEN** convertemos para API_Homolog
- **THEN** PAGE_Login NÃO deve ser incluído na conversão

#### Scenario: Include element in configuration

- **GIVEN** elemento PAGE_Login com `excluded_from: ["13051986534836779703"]`
- **AND** configuration Producao com `configuration_id: "2160971917577937056"`
- **WHEN** convertemos para Producao
- **THEN** PAGE_Login DEVE ser incluído na conversão

#### Scenario: Element in all configurations

- **GIVEN** elemento ServerProcedures com `excluded_from: []`
- **WHEN** convertemos para qualquer configuration
- **THEN** ServerProcedures DEVE ser incluído

---

### Requirement: Stack differentiation by configuration type

O sistema MUST gerar stacks diferentes baseado no tipo de configuration.

#### Scenario: Site WEBDEV generates templates

- **GIVEN** configuration Producao com `config_type: 2` (Site WEBDEV)
- **WHEN** convertemos para Producao
- **THEN** deve gerar:
  - `app/services/` ✅
  - `app/routes/` ✅
  - `app/templates/` ✅

#### Scenario: REST API skips templates

- **GIVEN** configuration API_Producao com `config_type: 23` (REST Webservice)
- **WHEN** convertemos para API_Producao
- **THEN** deve gerar:
  - `app/services/` ✅
  - `app/routes/` ✅
  - `app/templates/` ❌ (não gerar)

---

### Requirement: Integrate with code conversion

O sistema MUST substituir referências a variáveis configuráveis por `settings.VAR_NAME`.

#### Scenario: Replace variable reference

- **GIVEN** código usando `URL_API` que está no `ConfigurationContext`
- **WHEN** `WLanguageConverter.convert(code, config_context=context)` é chamado
- **THEN** código convertido deve usar `settings.URL_API`

#### Scenario: Remove COMPILE IF blocks from output

- **GIVEN** código com blocos `<COMPILE IF>...<END>`
- **WHEN** código é convertido
- **THEN** blocos devem ser removidos (conteúdo já está em config/)

#### Scenario: Add settings import

- **GIVEN** código que usa variáveis configuráveis
- **WHEN** service é gerado
- **THEN** deve incluir `from config import settings` nos imports

---

