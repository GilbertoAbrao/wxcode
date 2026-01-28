# Tasks: add-compile-if-extraction

> **Otimizado para Claude Sonnet 4.5**: Tasks pequenas, focadas, max 3-5 passos cada.

---

## Task 1: Criar dataclasses para CompileIfExtractor

**File:** `src/wxcode/parser/compile_if_extractor.py`

**Steps:**
1. Criar arquivo `compile_if_extractor.py`
2. Criar dataclass `CompileIfBlock` com campos: `conditions`, `operator`, `code`, `start_line`, `end_line`
3. Criar dataclass `ExtractedVariable` com campos: `name`, `value`, `var_type`, `configurations`

**Acceptance Criteria:**
- [x] Arquivo criado em `src/wxcode/parser/`
- [x] Dataclasses com type hints completos
- [x] Docstrings em português

---

## Task 2: Implementar regex do CompileIfExtractor

**File:** `src/wxcode/parser/compile_if_extractor.py`

**Steps:**
1. Criar classe `CompileIfExtractor`
2. Adicionar regex `COMPILE_IF_PATTERN` para detectar `<COMPILE IF Configuration="...">` e `<END>`
3. Implementar método `extract(code: str) -> list[CompileIfBlock]`

**Acceptance Criteria:**
- [x] Detecta `<COMPILE IF Configuration="X">`
- [x] Detecta `Configuration="X" OR Configuration="Y"`
- [x] Ignora blocos comentados (`//<COMPILE IF`)
- [x] Retorna lista de CompileIfBlock

---

## Task 3: Implementar extração de variáveis

**File:** `src/wxcode/parser/compile_if_extractor.py`

**Steps:**
1. Adicionar regex para detectar `CONSTANT X = "..."` e `gVar.X = "..."`
2. Implementar método `extract_variables(blocks: list[CompileIfBlock]) -> list[ExtractedVariable]`
3. Normalizar nomes: `gParams.URL` → `GPARAMS_URL`

**Acceptance Criteria:**
- [x] Extrai CONSTANT
- [x] Extrai atribuições globais
- [x] Nomes normalizados para UPPER_SNAKE_CASE

---

## Task 4: Criar model ConfigVariable

**File:** `src/wxcode/models/configuration_context.py`

**Steps:**
1. Criar arquivo `configuration_context.py`
2. Criar dataclass `ConfigVariable` com: `name`, `value`, `python_type`, `description`
3. Adicionar método `infer_python_type(value: str) -> str`

**Acceptance Criteria:**
- [x] Arquivo criado em `src/wxcode/models/`
- [x] Infere tipo: `"https://..."` → `str`, `123` → `int`

---

## Task 5: Criar model ConfigurationContext

**File:** `src/wxcode/models/configuration_context.py`

**Steps:**
1. Criar dataclass `ConfigurationContext` com: `variables_by_config`, `common_variables`, `configurations`
2. Implementar `from_blocks(blocks, variables) -> ConfigurationContext`
3. Implementar `get_variables_for_config(config_name) -> dict`

**Acceptance Criteria:**
- [x] Agrupa variáveis por configuration
- [x] Expande OR: `["A", "B"]` → variável em ambas configs
- [x] Método `get_variables_for_config` funciona

---

## Task 6: Criar model ConversionConfig

**File:** `src/wxcode/models/conversion_config.py`

**Steps:**
1. Criar arquivo `conversion_config.py`
2. Criar dataclass `ConversionConfig` com: `project_id`, `project_name`, `configuration_name`, `configuration_id`, `config_type`, `output_dir`
3. Adicionar properties: `is_site`, `is_api_only`, `should_generate_templates`

**Acceptance Criteria:**
- [x] `is_site` retorna `True` quando `config_type == 2`
- [x] `is_api_only` retorna `True` quando `config_type == 23`
- [x] `should_generate_templates` retorna `is_site`

---

## Task 7: Criar interface BaseConfigGenerator

**File:** `src/wxcode/generator/config_generator.py`

**Steps:**
1. Criar arquivo `config_generator.py`
2. Criar ABC `BaseConfigGenerator` com métodos abstratos:
   - `generate(context, output_dir) -> list[Path]`
   - `get_import_statement() -> str`
   - `get_variable_reference(var_name) -> str`

**Acceptance Criteria:**
- [x] ABC com `@abstractmethod` em todos os métodos
- [x] Type hints completos
- [x] Docstrings em português

---

## Task 8: Criar template settings.py.j2

**File:** `src/wxcode/generator/templates/python/config_settings.py.j2`

**Steps:**
1. Criar template Jinja2 para `config/settings.py`
2. Incluir classe `Settings(BaseSettings)` com variáveis dinâmicas
3. Incluir função `get_settings()` com `@lru_cache`

**Acceptance Criteria:**
- [x] Template gera código Python válido
- [x] Usa pydantic-settings
- [x] Variáveis tipadas

---

## Task 9: Criar templates env_file.j2 e config_init.py.j2

**Files:**
- `src/wxcode/generator/templates/python/env_file.j2`
- `src/wxcode/generator/templates/python/config_init.py.j2`

**Steps:**
1. Criar template `env_file.j2` para `.env` e `.env.example`
2. Criar template `config_init.py.j2` para `config/__init__.py`

**Acceptance Criteria:**
- [x] `.env` gerado com formato `VAR=value`
- [x] `__init__.py` exporta `settings` e `get_settings`

---

## Task 10: Implementar PythonConfigGenerator

**File:** `src/wxcode/generator/python_config_generator.py`

**Steps:**
1. Criar classe `PythonConfigGenerator(BaseConfigGenerator)`
2. Implementar `generate()` usando os templates criados
3. Gerar: `config/__init__.py`, `config/settings.py`, `.env`, `.env.example`

**Acceptance Criteria:**
- [x] Gera 4 arquivos
- [x] `get_import_statement()` retorna `"from config import settings"`
- [x] `get_variable_reference("URL")` retorna `"settings.URL"`

---

## Task 11: Adicionar config_context ao WLanguageConverter

**File:** `src/wxcode/generator/wlanguage_converter.py`

**Steps:**
1. Adicionar parâmetro `config_context: ConfigurationContext | None = None` ao `__init__`
2. Armazenar como `self._config_context`
3. Manter backward compatible (funciona sem context)

**Acceptance Criteria:**
- [x] Parâmetro opcional adicionado
- [x] Testes existentes continuam passando

---

## Task 12: Remover blocos COMPILE IF no WLanguageConverter

**File:** `src/wxcode/generator/wlanguage_converter.py`

**Steps:**
1. Adicionar regex para detectar `<COMPILE IF...>...<END>`
2. Em `convert()`, remover esses blocos antes de converter
3. Blocos removidos não aparecem no código Python

**Acceptance Criteria:**
- [x] Blocos `<COMPILE IF>` removidos do output
- [x] Código entre blocos preservado se relevante

---

## Task 13: Substituir variáveis por settings.X

**File:** `src/wxcode/generator/wlanguage_converter.py`

**Steps:**
1. Se `config_context` presente, obter lista de variáveis configuráveis
2. Ao encontrar referência a variável configurável, substituir por `settings.VAR_NAME`
3. Adicionar import `from config import settings` quando necessário

**Acceptance Criteria:**
- [x] `URL_API` vira `settings.URL_API`
- [x] Import adicionado automaticamente

---

## Task 14: Adicionar filtro de elementos no Orchestrator

**File:** `src/wxcode/generator/orchestrator.py`

**Steps:**
1. Adicionar método `_get_elements_for_config(config: ConversionConfig) -> list[Element]`
2. Query: `excluded_from` não contém `configuration_id`
3. Retornar apenas elementos incluídos na configuration

**Acceptance Criteria:**
- [x] Elementos com `excluded_from: [config_id]` são filtrados
- [x] Elementos com `excluded_from: []` são incluídos

---

## Task 15: Adicionar build de ConfigurationContext no Orchestrator

**File:** `src/wxcode/generator/orchestrator.py`

**Steps:**
1. Adicionar método `_build_config_context(elements, config_name) -> ConfigurationContext`
2. Usar `CompileIfExtractor` em cada elemento
3. Agregar variáveis de todos os elementos

**Acceptance Criteria:**
- [x] Extrai COMPILE IF de todos os elementos
- [x] Retorna ConfigurationContext consolidado

---

## Task 16: Atualizar convert() no Orchestrator

**File:** `src/wxcode/generator/orchestrator.py`

**Steps:**
1. Modificar `convert()` para receber `ConversionConfig`
2. Chamar `_get_elements_for_config()` para filtrar elementos
3. Chamar `_build_config_context()` para extrair configs
4. Condicionar `TemplateGenerator` a `config.should_generate_templates`

**Acceptance Criteria:**
- [x] type=2 gera templates
- [x] type=23 não gera templates
- [x] ConfigurationContext passado para generators

---

## Task 17: Adicionar --config ao CLI

**File:** `src/wxcode/cli.py`

**Steps:**
1. Adicionar opção `--config/-c` ao comando `convert`
2. Buscar configuration pelo nome no projeto
3. Criar output dir: `{output_base}/{config_name}/`
4. Criar `ConversionConfig` e chamar orchestrator

**Acceptance Criteria:**
- [x] `--config Producao` funciona
- [x] Output em `./output/Producao/`
- [x] Erro claro se config não existe

---

## Task 18: Adicionar --all-configs ao CLI

**File:** `src/wxcode/cli.py`

**Steps:**
1. Adicionar flag `--all-configs` ao comando `convert`
2. Iterar sobre todas as configurations do projeto
3. Converter cada uma para `{output_base}/{config_name}/`

**Acceptance Criteria:**
- [x] `--all-configs` converte todas
- [x] Cada config em sua pasta

---

## Task 19: Testes para CompileIfExtractor

**File:** `tests/test_compile_if_extractor.py`

**Steps:**
1. Testar extração de bloco simples
2. Testar extração com OR
3. Testar blocos comentados (ignorados)
4. Testar extração de variáveis

**Acceptance Criteria:**
- [x] 4 test cases passando (12 tests total)
- [x] Usar dados reais do Linkpay_ADM

---

## Task 20: Testes para ConfigurationContext e ConversionConfig

**File:** `tests/test_configuration_models.py`

**Steps:**
1. Testar `ConfigurationContext.from_blocks()`
2. Testar `get_variables_for_config()`
3. Testar `ConversionConfig` properties

**Acceptance Criteria:**
- [x] Testes para cada método/property (19 tests total)
- [x] Edge cases cobertos

---

## Task 21: Testes para PythonConfigGenerator

**File:** `tests/test_python_config_generator.py`

**Steps:**
1. Testar geração de `settings.py`
2. Testar geração de `.env`
3. Verificar código gerado é válido Python

**Acceptance Criteria:**
- [x] Arquivos gerados são válidos (13 tests total)
- [x] `python -m py_compile` passa

---

## Task 22: Teste de integração

**Command:** `wxcode convert Linkpay_ADM --all-configs`

**Steps:**
1. Executar conversão de todas as configs
2. Verificar estrutura de pastas
3. Verificar type=2 tem templates, type=23 não tem
4. Verificar services usam `settings.X`

**Acceptance Criteria:**
- [x] Sem erros de execução
- [x] Estrutura correta por tipo
- [x] Código Python válido (config files)

---

## Dependencies Graph

```
Group 1 (Parallel):     1 → 2 → 3 (Extractor)
                        4 → 5 (Context)
                        6 (ConversionConfig)
                        7 (Interface)

Group 2 (Parallel):     8 → 9 → 10 (PythonGen)
                        11 → 12 → 13 (WLanguageConverter)

Group 3 (Sequential):   14 → 15 → 16 (Orchestrator)
                        17 → 18 (CLI)

Group 4 (Parallel):     19, 20, 21 (Tests)

Final:                  22 (Integration)
```

---

💡 **Dica:** Antes de executar `/openspec:apply`, confirme que está usando Sonnet 4.5:
- Verifique com `/status`
- Ou troque com `/model sonnet`
