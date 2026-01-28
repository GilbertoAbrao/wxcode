# Tasks: Add Procedure Parser

## 1. Model Layer
- [x] 1.1 Create `Procedure` Beanie model with fields: name, parameters, return_type, code, element_id, dependencies
- [x] 1.2 Create `ProcedureParameter` embedded model for parameter details
- [x] 1.3 Export new models in `models/__init__.py`

## 2. Parser Implementation
- [x] 2.1 Create `WdgParser` class in `parser/wdg_parser.py`
- [x] 2.2 Implement YAML-like parsing for .wdg file structure
- [x] 2.3 Extract procedure metadata (name, type_code, procedure_id)
- [x] 2.4 Parse procedure signature (parameters, return type)
- [x] 2.5 Extract procedure code body
- [x] 2.6 Parse structures defined in procedure_set (STFlatJson, etc)

## 3. Dependency Analysis
- [x] 3.1 Extract procedure calls within code (regex for function calls)
- [x] 3.2 Extract HyperFile operations (HReadFirst, HAdd, etc)
- [x] 3.3 Extract external API calls (HTTPRequest, RESTSend)
- [x] 3.4 Store dependencies in procedure document

## 4. CLI Integration
- [x] 4.1 Add `parse-procedures` command to CLI
- [x] 4.2 Support batch processing of .wdg files
- [x] 4.3 Update element's `ast` field with parsed procedures

## 5. Testing
- [x] 5.1 Unit tests for WdgParser with Util.wdg sample
- [x] 5.2 Integration test with project-refs/Linkpay_ADM
- [x] 5.3 Test edge cases (empty procedures, complex signatures)

## 6. Documentation
- [x] 6.1 Update CLAUDE.md with procedure parsing info
- [x] 6.2 Add docstrings to new modules
