# Tasks: extract-database-connections

## Phase 1: Parser Updates

### Task 1.1: Add Connection Type Mapping
**File:** `src/wxcode/parser/xdd_parser.py`

- [x] Criar `CONNECTION_TYPE_MAP` com mapeamento Type → (database_type, driver_name, default_port)
- [x] Tipos a mapear: 1=sqlserver, 2=mysql, 3=postgresql, 4=oracle, 5=hyperfile, 6=hyperfile_cs
- [x] Adicionar método `_map_connection_type(type_code: int) -> tuple[str, str, str]`

**Validation:** Unit test com diferentes Type codes

### Task 1.2: Update SchemaConnection Model
**File:** `src/wxcode/models/schema.py`

- [x] Adicionar campo `database_type: str = ""`
- [x] Adicionar campo `driver_name: str = ""`
- [x] Adicionar campo `port: str = ""`
- [x] Adicionar campo `extended_info: str = ""`

**Validation:** Verificar schema migration não quebra dados existentes

### Task 1.3: Update Connection Parsing
**File:** `src/wxcode/parser/xdd_parser.py`

- [x] Atualizar `_parse_connections()` para chamar `_map_connection_type()`
- [x] Extrair INFOS_ETENDUES e armazenar em `extended_info`
- [x] Extrair porta de INFOS_ETENDUES ou usar default do mapeamento
- [x] Adicionar warning para tipos desconhecidos
- [x] Adicionar método `_extract_port_from_extended_info()` para parsing de porta

**Validation:** `pytest tests/parser/test_xdd_parser.py -v`

---

## Phase 2: StarterKit Updates

### Task 2.1: Pass Connections to StarterKit
**File:** `src/wxcode/generator/orchestrator.py`

- [x] Carregar DatabaseSchema do MongoDB antes de gerar starter kit
- [x] Adicionar método `_load_database_connections()` assíncrono
- [x] Passar connections para `_generate_database_py()`, `_generate_env_example()`, `_generate_pyproject_toml()`
- [x] Tornar `_generate_project_structure()` assíncrono
- [x] Atualizar `convert_with_config()` para também usar async `_generate_project_structure()`

**Validation:** Integration test com projeto que tem schema parseado

### Task 2.2: Dynamic .env.example Generation
**Files:** `src/wxcode/generator/orchestrator.py`, `src/wxcode/generator/starter_kit.py`

- [x] Atualizar `_generate_env_example()` em orchestrator para receber connections
- [x] Atualizar `_generate_env_example()` em starter_kit para usar `config.connections`
- [x] Gerar variáveis por conexão: `{NAME}_HOST`, `{NAME}_PORT`, `{NAME}_DATABASE`, etc.
- [x] Adicionar comentário para cada seção de conexão
- [x] Manter fallback para MongoDB quando não há connections

**Validation:** Verificar .env.example gerado contém variáveis corretas

### Task 2.3: Dynamic requirements.txt Generation
**Files:** `src/wxcode/generator/orchestrator.py`, `src/wxcode/generator/starter_kit.py`

- [x] Atualizar `_generate_pyproject_toml()` em orchestrator para incluir drivers por tipo de banco
- [x] Atualizar `_generate_requirements_txt()` em starter_kit para usar `config.connections`
- [x] Mapear database_type para pacotes necessários (aioodbc, asyncpg, aiomysql, oracledb)
- [x] Evitar duplicação de pacotes comuns (sqlalchemy)
- [x] Adicionar SQLAlchemy quando qualquer banco SQL é usado

**Validation:** requirements.txt/pyproject.toml incluem drivers corretos para cada tipo de banco

### Task 2.4: Multi-Connection database.py Generation
**Files:** `src/wxcode/generator/orchestrator.py`, `src/wxcode/generator/starter_kit.py`

- [x] Atualizar `_generate_database_py()` em orchestrator para suportar múltiplas conexões
- [x] Atualizar `_generate_database_py()` em starter_kit para usar `config.connections`
- [x] Gerar dict `connections: dict[str, dict]` com engine e session_factory
- [x] Gerar `get_db(connection_name: str)` com seleção por nome
- [x] Manter fallback para MongoDB quando não há connections
- [x] Adicionar comentários para conexões HyperFile (não suportadas)

**Validation:** database.py gerado importa corretamente e inicializa conexões

### Task 2.5: Update StarterKitConfig
**File:** `src/wxcode/generator/starter_kit.py`

- [x] Adicionar campo `connections: list[Any]` ao StarterKitConfig
- [x] Manter compatibilidade com uso sem connections (fallback para use_mongodb)

**Validation:** Geração funciona com e sem connections

---

## Phase 3: Tests

### Task 3.1: Unit Tests for Parser
**File:** `tests/test_xdd_parser.py`

- [x] Test `test_map_connection_type_sqlserver`
- [x] Test `test_map_connection_type_mysql`
- [x] Test `test_map_connection_type_postgresql`
- [x] Test `test_map_connection_type_oracle`
- [x] Test `test_map_connection_type_hyperfile`
- [x] Test `test_map_connection_type_hyperfile_cs`
- [x] Test `test_map_connection_type_unknown`
- [x] Test `test_extract_port_from_extended_info_port_param`
- [x] Test `test_extract_port_from_extended_info_server_comma_format`
- [x] Test `test_extract_port_from_extended_info_empty_string`
- [x] Test `test_parse_connection_with_extended_info`
- [x] Test `test_parse_connection_default_port`
- [x] Test `test_parse_connection_no_extended_info`
- [x] Test `test_parse_multiple_connections`

**Status:** ✅ COMPLETO - Adicionados à classe `TestConnectionTypeMapping`, `TestExtractPortFromExtendedInfo` e `TestParseConnectionsWithExtendedInfo`

### Task 3.2: Unit Tests for StarterKit
**File:** `tests/test_starter_kit.py` (novo arquivo criado)

- [x] Test `test_generate_env_single_connection`
- [x] Test `test_generate_env_multiple_connections`
- [x] Test `test_generate_env_no_connections_fallback`
- [x] Test `test_generate_requirements_with_sqlserver_driver`
- [x] Test `test_generate_requirements_with_multiple_drivers`
- [x] Test `test_generate_requirements_no_connections_fallback`
- [x] Test `test_generate_database_single_connection`
- [x] Test `test_generate_database_multiconn`
- [x] Test `test_generate_database_no_connections_mongodb_fallback`
- [x] Test `test_generate_database_hyperfile_connection_commented`

**Status:** ✅ COMPLETO - Classes `TestGenerateEnvExample`, `TestGenerateRequirementsTxt`, `TestGenerateDatabasePy`

### Task 3.3: Integration Test
**File:** `tests/integration/test_database_connections_pipeline.py` (novo arquivo criado)

- [x] Test `test_parse_xdd_extracts_connection_metadata`
- [x] Test `test_orchestrator_loads_connections_from_mongodb`
- [x] Test `test_orchestrator_generates_env_with_connections`
- [x] Test `test_orchestrator_generates_database_with_connections`
- [x] Test `test_orchestrator_generates_requirements_with_drivers`
- [x] Test `test_no_connections_fallback_to_mongodb`
- [x] Test `test_unknown_connection_type_warning`
- [x] Test `test_hyperfile_connection_no_sqlalchemy_imports`

**Status:** ✅ COMPLETO - Classe `TestDatabaseConnectionsPipeline` e `TestConnectionTypeEdgeCases`

---

## Dependencies

```
Task 1.2 → Task 1.1 (model precisa dos novos campos)
Task 1.3 → Task 1.1, 1.2 (parser usa o mapeamento e modelo)
Task 2.1 → Task 1.3 (orchestrator precisa das conexões parseadas)
Task 2.2, 2.3, 2.4 → Task 2.1 (StarterKit recebe as conexões)
Task 3.* → Paralelo após Phase 2
```

## Parallelizable Work

- Task 1.1 e Task 1.2 podem rodar em paralelo
- Task 2.2, 2.3, 2.4 podem rodar em paralelo após Task 2.1
- Task 3.1, 3.2, 3.3 podem rodar em paralelo
