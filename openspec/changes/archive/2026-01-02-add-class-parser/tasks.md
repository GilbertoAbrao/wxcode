# Tasks: add-class-parser

## Overview
Parser para arquivos .wdc (classes WinDev) que extrai estrutura completa: herança, membros, métodos, constantes.

## Task List

### 1. Create Class Models
**File**: `src/wxcode/models/class_definition.py`

- [x] 1.1 Create `ClassMember` embedded model (name, type, visibility, default_value, serialize)
- [x] 1.2 Create `ClassConstant` embedded model (name, value, type)
- [x] 1.3 Create `ClassMethod` embedded model (reutiliza ProcedureParameter)
- [x] 1.4 Create `ClassDependencies` embedded model
- [x] 1.5 Create `ClassDefinition` Beanie Document
- [x] 1.6 Export models in `__init__.py`
- [x] 1.7 Register `ClassDefinition` in `database.py`

**Validation**: Models importable, type hints correct

---

### 2. Implement WdcParser
**File**: `src/wxcode/parser/wdc_parser.py`

- [x] 2.1 Create regex patterns (CLASS_DEF_RE, INHERITS_RE, VISIBILITY_BLOCK_RE, MEMBER_RE)
- [x] 2.2 Create `ParsedClass` dataclass for intermediate result
- [x] 2.3 Implement `__init__()` with path validation
- [x] 2.4 Implement `_parse_class_definition()` - extrai nome, abstract, herança
- [x] 2.5 Implement `_parse_members()` - extrai membros com visibilidade
- [x] 2.6 Implement `_parse_methods()` - extrai procedures como métodos
- [x] 2.7 Implement `_extract_dependencies()` - identifica classes e arquivos usados
- [x] 2.8 Implement `parse()` main method
- [x] 2.9 Export in parser `__init__.py`

**Validation**: Parser returns correct data for classUsuario.wdc

---

### 3. Add CLI Command
**File**: `src/wxcode/cli.py`

- [x] 3.1 Create `parse_classes` command with Typer
- [x] 3.2 Implement discovery of .wdc files in project
- [x] 3.3 Implement project lookup in MongoDB
- [x] 3.4 Implement idempotent save (delete old + insert new)
- [x] 3.5 Display summary statistics (classes, métodos, membros)
- [x] 3.6 Display inheritance tree preview
- [x] 3.7 Handle errors gracefully

**Validation**: `wxcode parse-classes ./project-refs/Linkpay_ADM` works

---

### 4. Create Unit Tests
**File**: `tests/test_wdc_parser.py`

- [x] 4.1 Create sample .wdc fixture (classe simples)
- [x] 4.2 Create fixture with herança
- [x] 4.3 Test `_parse_class_definition()` - nome, abstract, herança
- [x] 4.4 Test `_parse_members()` - visibilidade, tipos, defaults
- [x] 4.5 Test `_parse_methods()` - constructor, destructor, métodos
- [x] 4.6 Test `_extract_dependencies()`
- [x] 4.7 Test classe abstrata
- [x] 4.8 Test encoding ISO-8859-1

**Validation**: `pytest tests/test_wdc_parser.py` passes

---

### 5. End-to-End Test
- [x] 5.1 Run `parse-classes` on Linkpay_ADM
- [x] 5.2 Verify all 14 classes extracted
- [x] 5.3 Verify herança de `_classBasic` detectada
- [x] 5.4 Verify métodos de `_classBasic` (Salvar, Get, Validar, Excluir)
- [x] 5.5 Verify membros com visibilidade
- [x] 5.6 Verify MongoDB documents created

**Validation**: All data matches .wdc content

---

### 6. Documentation
- [x] 6.1 Update CLAUDE.md with parse-classes command
- [x] 6.2 Update CLAUDE.md status table
- [x] 6.3 Update file reference table

**Validation**: Documentation accurate and complete

---

## Dependencies
- Task 1 must complete before Task 2
- Task 2 must complete before Task 3
- Tasks 4-6 can run in parallel after Task 3

## Estimated Scope
- Models: ~120 lines
- Parser: ~250 lines
- CLI: ~100 lines
- Tests: ~300 lines
- **Total**: ~770 lines
