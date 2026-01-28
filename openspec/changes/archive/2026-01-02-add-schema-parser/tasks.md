# Tasks: add-schema-parser

## Overview
Parser para arquivos .xdd (Analysis WinDev) que extrai schema de banco de dados.

## Task List

### 0. Fix analysis_path Capture in ProjectMapper ✅
**File**: `src/wxcode/parser/project_mapper.py`

O `analysis_path` não está sendo capturado porque a linha `analysis : .\BD.ana\BD.wda` vem depois da seção `configurations` no arquivo .wwp.

- [x] 0.1 Modificar `_extract_header_metadata()` para continuar lendo após `configurations`
- [x] 0.2 Adicionar lógica para capturar `analysis` em qualquer posição do arquivo
- [x] 0.3 Testar que `Project.analysis_path` é salvo corretamente

**Validation**: Após re-import, `analysis_path` deve conter `.\BD.ana\BD.wda`

---

### 1. Create Schema Models ✅
**File**: `src/wxcode/models/schema.py`

- [x] 1.1 Create `SchemaConnection` embedded model
- [x] 1.2 Create `SchemaColumn` embedded model with type mapping
- [x] 1.3 Create `SchemaIndex` embedded model
- [x] 1.4 Create `SchemaTable` embedded model
- [x] 1.5 Create `DatabaseSchema` Beanie Document
- [x] 1.6 Export models in `__init__.py`
- [x] 1.7 Register `DatabaseSchema` in `database.py`

**Validation**: Models importable, type hints correct

---

### 2. Implement XddParser ✅
**File**: `src/wxcode/parser/xdd_parser.py`

- [x] 2.1 Create `HYPERFILE_TYPE_MAP` constant (16 types)
- [x] 2.2 Create `XddParseResult` dataclass
- [x] 2.3 Implement `XddParser.__init__()` with path validation
- [x] 2.4 Implement `_parse_connections()` method
- [x] 2.5 Implement `_parse_columns()` method with type mapping
- [x] 2.6 Implement `_parse_tables()` method
- [x] 2.7 Implement `_infer_indexes()` from columns
- [x] 2.8 Implement `parse()` main method
- [x] 2.9 Handle ISO-8859-1 encoding

**Validation**: Parser returns correct data for sample XML

---

### 3. Add CLI Command ✅
**File**: `src/wxcode/cli.py`

- [x] 3.1 Create `find_analysis_file()` helper function
- [x] 3.2 Create `parse_schema` command with Typer
- [x] 3.3 Implement project lookup in MongoDB
- [x] 3.4 Implement idempotent save (delete old + insert new)
- [x] 3.5 Display summary statistics
- [x] 3.6 Handle errors gracefully

**Validation**: `wxcode parse-schema ./project-refs/Linkpay_ADM` works

---

### 4. Create Unit Tests ✅
**File**: `tests/test_xdd_parser.py`

- [x] 4.1 Create sample XML fixture
- [x] 4.2 Test `_parse_connections()` extraction
- [x] 4.3 Test `_parse_columns()` with all 16 types
- [x] 4.4 Test `_parse_tables()` with nested data
- [x] 4.5 Test type mapping (HyperFile → Python)
- [x] 4.6 Test PK/Index detection (TYPE_CLE)
- [x] 4.7 Test nullable/default extraction
- [x] 4.8 Test unknown type handling (warning + Any)
- [x] 4.9 Test encoding handling

**Validation**: `pytest tests/test_xdd_parser.py` passes - 29 tests passed

---

### 5. End-to-End Test ✅
- [x] 5.1 Run `parse-schema` on Linkpay_ADM
- [x] 5.2 Verify 50 tables extracted
- [x] 5.3 Verify 942 columns extracted
- [x] 5.4 Verify 2 connections extracted
- [x] 5.5 Spot-check type mappings (IDcliente → int, RazaoSocial → str)
- [x] 5.6 Verify MongoDB document created

**Validation**: All data matches BD.xdd content

---

### 6. Documentation ✅
- [x] 6.1 Update CLAUDE.md with parse-schema command
- [x] 6.2 Update CLAUDE.md status and file references
- [x] 6.3 Mark all tasks as completed in tasks.md

**Validation**: Documentation accurate and complete

---

## Dependencies
- Task 0 should be done first (fix analysis_path)
- Task 1 must complete before Task 2
- Task 2 must complete before Task 3
- Tasks 4-6 can run in parallel after Task 3

## Estimated Scope
- ProjectMapper fix: ~20 lines
- Models: ~100 lines
- Parser: ~200 lines
- CLI: ~80 lines
- Tests: ~300 lines
- **Total**: ~700 lines
