# Tasks: expand-enrich-dependencies

## Overview
Expandir o comando `enrich` para extrair procedures locais e dependências de páginas/windows.

## Task List

### 1. Create DependencyExtractor
**File**: `src/wxcode/parser/dependency_extractor.py`

- [x] 1.1 Create `ExtractedDependencies` dataclass
- [x] 1.2 Create `DependencyExtractor` class
- [x] 1.3 Consolidate regex from wdg_parser and wdc_parser (PROCEDURE_CALL_RE, HYPERFILE_RE)
- [x] 1.4 Add CLASS_USAGE_RE for class detection
- [x] 1.5 Add REST_API_RE for API detection
- [x] 1.6 Implement `extract(code: str)` method
- [x] 1.7 Implement `merge(*deps)` method to combine dependencies
- [x] 1.8 Add comprehensive BUILTIN_FUNCTIONS set
- [x] 1.9 Export in parser `__init__.py`

**Validation**: ✅ DependencyExtractor can extract deps from sample code

---

### 2. Modify Procedure Model
**File**: `src/wxcode/models/procedure.py`

- [x] 2.1 Add `is_local: bool = False` field
- [x] 2.2 Add `scope: Optional[str] = None` field (page, window, report)
- [x] 2.3 Add index for `is_local` field
- [x] 2.4 Update docstrings

**Validation**: ✅ Model accepts new fields, existing data unaffected

---

### 3. Expand WWHParser for Local Procedures
**File**: `src/wxcode/parser/wwh_parser.py`

- [x] 3.1 Create `ParsedLocalProcedure` dataclass
- [x] 3.2 Add `local_procedures: list[ParsedLocalProcedure]` to `ParsedPage`
- [x] 3.3 Implement `_extract_local_procedures()` method
- [x] 3.4 Parse procedure signature (name, parameters, return_type)
- [x] 3.5 Extract procedure code body
- [x] 3.6 Count code lines
- [x] 3.7 Call extraction in `parse()` method

**Validation**: ✅ WWHParser extracts local procedures

---

### 4. Expand ElementEnricher
**File**: `src/wxcode/parser/element_enricher.py`

- [x] 4.1 Import DependencyExtractor
- [x] 4.2 Add `dep_extractor` instance to __init__
- [x] 4.3 Implement `_process_local_procedures()` method
- [x] 4.4 Implement `_extract_all_dependencies()` method
- [x] 4.5 Modify `_enrich_element()` to call new methods
- [x] 4.6 Update `Element.dependencies` with extracted data
- [x] 4.7 Add `local_procedures_created` to `EnrichmentResult`
- [x] 4.8 Add `dependencies_extracted` to `EnrichmentStats`

**Validation**: ✅ Enrich command extracts procedures and dependencies

---

### 5. Update CLI Output
**File**: `src/wxcode/cli.py`

- [x] 5.1 Update enrich progress to show local procedures count
- [x] 5.2 Update summary to show total local procedures
- [x] 5.3 Update summary to show dependencies extracted
- [x] 5.4 Handle errors gracefully

**Validation**: ✅ CLI shows new statistics

---

### 6. Create Unit Tests
**File**: `tests/test_dependency_extractor.py`

- [x] 6.1 Test PROCEDURE_CALL_RE extraction
- [x] 6.2 Test HYPERFILE_RE extraction
- [x] 6.3 Test CLASS_USAGE_RE extraction
- [x] 6.4 Test REST_API_RE extraction
- [x] 6.5 Test BUILTIN_FUNCTIONS filtering
- [x] 6.6 Test merge() method
- [x] 6.7 Test with real code samples

**Validation**: ✅ `pytest tests/test_dependency_extractor.py` passes (28 tests)

---

### 7. Create WWHParser Tests
**File**: `tests/test_wwh_parser.py`

- [x] 7.1 Create fixture with local procedures
- [x] 7.2 Test `_extract_local_procedures()`
- [x] 7.3 Test procedure signature parsing
- [x] 7.4 Test procedure with parameters
- [x] 7.5 Test procedure with return type

**Validation**: ✅ `pytest tests/test_wwh_parser.py` passes (22 tests)

---

### 8. End-to-End Test
- [ ] 8.1 Run `enrich` on Linkpay_ADM
- [ ] 8.2 Verify local procedures saved (should be ~207)
- [ ] 8.3 Verify `Procedure.is_local = True` for page procedures
- [ ] 8.4 Verify `Element.dependencies` populated
- [ ] 8.5 Verify dependencies include procedures, tables, classes
- [ ] 8.6 Verify MongoDB data consistency

**Validation**: Pending - requires `wxcode import` first

---

### 9. Documentation
- [x] 9.1 Update CLAUDE.md with expanded enrich functionality
- [x] 9.2 Update status table
- [x] 9.3 Update file reference table

**Validation**: ✅ Documentation accurate and complete

---

## Dependencies
- Task 1 must complete before Tasks 3, 4
- Task 2 can run in parallel with Task 1
- Task 3 must complete before Task 4
- Task 4 depends on Tasks 1, 2, 3
- Task 5 depends on Task 4
- Tasks 6, 7 can run in parallel after Task 4
- Task 8 depends on Tasks 4, 5
- Task 9 can run after Task 8

## Parallelization
```
Task 1 ──┬──► Task 3 ──► Task 4 ──┬──► Task 5 ──► Task 8 ──► Task 9
Task 2 ──┘                        ├──► Task 6
                                  └──► Task 7
```

## Estimated Scope
- DependencyExtractor: ~120 lines ✅
- Procedure model changes: ~20 lines ✅
- WWHParser changes: ~100 lines ✅
- ElementEnricher changes: ~150 lines ✅
- CLI changes: ~30 lines ✅
- Tests: ~250 lines ✅
- **Total**: ~670 lines ✅
