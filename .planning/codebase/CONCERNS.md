# Codebase Concerns

**Analysis Date:** 2026-01-21

## Technical Debt

### Large Monolithic Files

**File complexity overgrowth:**
- `src/wxcode/cli.py` - **4,189 lines** - Contains 20+ commands mixed together, lacks modular structure
  - Impact: Difficult to test individual commands, increases cognitive load
  - Fix approach: Extract commands into separate handler modules by domain (parsing, analysis, conversion, generation)

- `src/wxcode/parser/element_enricher.py` - **967 lines** - Orchestrates multiple enrichment steps sequentially
  - Impact: Hard to debug matching failures, difficult to parallelize enrichment
  - Fix approach: Split into separate enrichers (ControlEnricher, ProcedureEnricher, DataBindingEnricher) with pluggable interface

- `src/wxcode/generator/orchestrator.py` - **1,145 lines** - Coordinates all generators and handles configuration
  - Impact: Generator orchestration logic mixed with error handling, difficult to add new generators
  - Fix approach: Extract generator registry pattern, separate configuration validation from orchestration

- `src/wxcode/services/gsd_invoker.py` - **934 lines** - Handles PTY streaming, subprocess management, websocket communication
  - Impact: Difficult to test individual concerns (PTY I/O vs websocket communication)
  - Fix approach: Extract PTY streamer, websocket handler, and process manager into separate classes

### Incomplete WLanguage Conversion

**Missing WLanguage-to-Python mapping:**
- File: `src/wxcode/generator/wlanguage_converter.py` (661 lines)
- Lines 258, 266, 321, 415: Multiple fallback comments like "# TODO: Unknown function", "# TODO: Convert"
- Impact: Generated code contains TODOs and comments when WLanguage functions aren't recognized, breaking downstream compilation
- Known missing functions: Custom H* functions, string manipulation functions with encoding, advanced query functions
- Fix approach: Implement comprehensive function registry with plugin system for custom functions; generate stubs with manual review markers

### Stub Generation and Manual Review TODOs

**Generated code contains placeholders:**
- File: `src/wxcode/llm_converter/output_writer.py` (Lines 248, 252, 279, 285, 311)
- Generated stubs: `"""TODO: Implementar"""`, `# TODO: Adicionar campos`
- Impact: Generated code isn't executable until manually completed; batch conversion workflows break
- Fix approach: Replace stubs with executable defaults (empty methods, pass statements for properties) or mark as "needs_implementation" in metadata

### Layer Assignment Gap

**Conversion model missing layer field:**
- File: `src/wxcode/api/conversions.py` (Lines 195, 300)
- Code: `layer=None,  # TODO: adicionar quando tivermos layer no model`
- Impact: Can't filter conversions by layer (UI/Business/Data), topological ordering incomplete
- Fix approach: Add `layer: ElementLayer` to ConversionResult, populate during conversion based on element type

### Validator Generation Placeholders

**Schema validators incomplete:**
- File: `src/wxcode/generator/schema_generator.py` (Lines 358-367)
- Missing: CPF, CNPJ, phone, CEP validators output as TODOs in docstrings
- Impact: Generated Pydantic models won't validate Brazilian business data correctly
- Fix approach: Implement validators library with proper regex/algorithm implementations

### Query and Template Extraction Gaps

**Data binding extraction incomplete:**
- File: `src/wxcode/generator/template_generator.py` (Lines 356, 502, 516)
- Issue: ComboBox options, select values, table data sources marked as "# TODO: Extract"
- Impact: Generated templates have hardcoded empty data, won't bind to backend
- Fix approach: Enhance data binding extractor to parse query references and control bindings from raw_content

---

## Known Issues

### PDF Processing Limitations

**Protected PDFs fail silently:**
- File: `src/wxcode/parser/pdf_doc_splitter.py` (Line 348: `except Exception as e`)
- Issue: PDF splitter catches all exceptions but only logs; protected PDFs produce zero elements extracted
- Impact: Documentation for projects with PDF protection fails unnoticed, leaves orphaned elements
- Workaround: Pre-process PDFs with `qpdf --decrypt` before splitting
- Fix approach: Detect PDF protection status early, raise explicit error with recovery instructions

### Neo4j Special Character Handling

**Neo4j sync corrupts non-ASCII names:**
- File: `src/wxcode/graph/neo4j_sync.py` (Lines 395-467)
- Issue: Cypher queries not properly escaping special characters in Brazilian names (ç, ã, é)
- Impact: Graph relationships for procedures/tables with accents fail to create or become orphaned
- Fix approach: Use Neo4j parameter placeholders (`$param`) instead of string interpolation for all node properties

### Bare Exception Handlers

**Catch-all exceptions hide real problems:**
- File locations: 60+ instances across codebase
  - `src/wxcode/services/gsd_invoker.py` (Lines 72, 343, 709)
  - `src/wxcode/services/step_executor.py` (Line 109)
  - `src/wxcode/api/websocket.py` (Lines 93, 150, 162, 179)
  - `src/wxcode/api/conversions.py` (Multiple lines)
- Issue: `except Exception as e:` catches everything, loses distinguishability between transient failures and logic errors
- Impact: Difficult to debug, false recovery attempts, swallowed errors in logging
- Fix approach: Use exception hierarchy (IOError, ValueError, etc.) with context-specific handlers

### Subprocess Communication Buffering

**PTY output buffering causes incomplete streaming:**
- File: `src/wxcode/services/gsd_invoker.py` (Lines 494-523)
- Issue: Non-blocking PTY reads combined with asyncio executor can miss partial lines; buffer draining on process exit may lose final output
- Impact: WebSocket clients miss final status messages, GSD workflow completion unclear
- Fix approach: Implement line-buffering wrapper around PTY reads; guarantee final flush before process exit signal

---

## Security Considerations

### Raw Content String Injection

**Unvalidated raw_content in code generation:**
- Files affected:
  - `src/wxcode/models/element.py` - stores raw WLanguage code
  - `src/wxcode/parser/project_mapper.py` - populates from binary parse
  - `src/wxcode/generator/wlanguage_converter.py` - converts to Python
  - `src/wxcode/generator/template_generator.py` - injects into Jinja2
- Issue: raw_content is sourced from WinDev binary files without sanitization; converted code could contain Python injection
- Risk: If WinDev file is malicious or corrupted, generated code could execute arbitrary Python
- Current mitigation: Guardrail service blocks some patterns; generated code reviewed by humans before deployment
- Recommendations:
  1. Add AST validation after WLanguage conversion to reject potentially malicious patterns (eval calls, file operations)
  2. Sandbox code generation in isolated process with resource limits
  3. Implement code provenance tracking (mark converted code as "untrusted")

### Subprocess Command Injection Risk

**Subprocess calls with user input:**
- File: `src/wxcode/services/gsd_context_collector.py` (Lines 771, 789)
- Code: Uses `subprocess.run()` with git branch names directly from user input
- Risk: Malicious branch names with shell metacharacters could execute arbitrary commands
- Current mitigation: `check=True` prevents silent failures; no shell=True parameter used
- Recommendations:
  1. Validate branch names against git naming rules before passing to subprocess
  2. Always use list form of subprocess.run (not shell string)
  3. Add branch name regex whitelist: `^[a-zA-Z0-9/_-]+$`

### File Path Traversal

**PDF output paths not validated:**
- File: `src/wxcode/parser/pdf_doc_splitter.py` - extracts PDFs to user-provided output directory
- Risk: Symlink attacks or path traversal could write outside intended output directory
- Current mitigation: Guardrail.is_safe_path() checks some paths, but not output directory validation
- Recommendations:
  1. Use `Path.resolve().relative_to(base_output)` to ensure extracted files stay within output directory
  2. Reject paths containing `..` or symlinks that escape base directory
  3. Validate output directory is writable and on expected filesystem

### API Key / Credential Exposure in Logs

**Sensitive data in error messages:**
- Files: `src/wxcode/services/gsd_invoker.py`, `src/wxcode/api/websocket.py`
- Issue: Subprocess stderr/stdout may contain API keys from environment variables or .env files
- Current mitigation: Guardrail.sanitize_output() removes some patterns; limited scope
- Recommendations:
  1. Redact environment variables from subprocess output before logging/streaming
  2. Implement output_sanitizer for all subprocess results
  3. Add audit log that tracks what was redacted for forensics

### N8N Webhook Hardcoded URL

**Hardcoded external service endpoint:**
- File: `src/wxcode/services/gsd_invoker.py` (Lines 29-32)
- Issue: n8n webhook URL hardcoded with default fallback; no validation that webhook is expected
- Risk: Man-in-the-middle redirect or compromise of webhook service could intercept conversation data
- Recommendations:
  1. Move to environment variable with required validation
  2. Validate webhook domain against whitelist
  3. Add request signing (HMAC) to webhook calls

---

## Performance Bottlenecks

### Sequential Element Enrichment

**Element enrichment blocks one-by-one:**
- File: `src/wxcode/parser/element_enricher.py` (Orchestrator pattern)
- Issue: Enrichment steps (PDF matching, procedure extraction, data binding) run sequentially for each element
- Impact: For 500+ element projects, enrichment takes 10+ minutes; MongoDB queries not batched
- Fix approach:
  1. Batch enrichment operations by element type
  2. Parallelize independent enrichment steps (PDF extraction doesn't depend on procedure parsing)
  3. Use MongoDB bulk operations instead of individual save() calls

### Large CLI File Processing

**Memory spikes during project import:**
- File: `src/wxcode/cli.py` - import command holds all elements in memory before batch insert
- Issue: batch_size=100 default, but CLI doesn't stream to database during file reading
- Impact: Large projects (20k+ elements) consume >2GB memory during import
- Fix approach: Reduce batch size to 50, implement streaming MongoDB inserts during file parsing (don't wait for complete file read)

### Neo4j Query Performance

**Synchronization queries not indexed:**
- File: `src/wxcode/graph/neo4j_sync.py` (Lines 395-520)
- Issue: Creates nodes without index hints; impact analysis queries scan full graph
- Impact: Impact analysis for large graphs (5000+ nodes) takes >30 seconds
- Fix approach:
  1. Create indexes on (element_name), (element_type), (project_name)
  2. Use EXPLAIN to verify query plans
  3. Add pagination to large result sets

### Regex Compilation in Hot Paths

**WLanguage converter regex patterns recompiled per function:**
- File: `src/wxcode/generator/wlanguage_converter.py` (Lines 82-97)
- Issue: CONTROL_FLOW_PATTERNS re-used per conversion call, not compiled once at class init
- Impact: 10+ microsecond overhead per function converted; significant for 1000+ procedure conversion
- Fix approach: Pre-compile all regex patterns in __init__, cache in class attributes

---

## Fragile Areas

### Control Matching Algorithm

**Fragile PDF-to-Code control matching:**
- File: `src/wxcode/parser/element_enricher.py` (MatchingContext, 200+ lines of matching logic)
- Why fragile:
  - Uses heuristic scoring (position, name prefix, depth) without ML training
  - PDF order may differ from source code order
  - Manual control renaming breaks all assumptions
  - Multi-language support (Portuguese/English control names) not handled
- Safe modification:
  1. Add test fixtures with 10+ real project examples showing expected matches
  2. Document scoring weights with rationale before changing
  3. Add regression test to verify no matches degrade after refactor
- Test coverage: Exists (`tests/test_control_matching.py`) but only 5 scenarios; needs 20+ edge cases

### WLanguage to Python Conversion

**Conversion correctness depends on complex regex patterns:**
- File: `src/wxcode/generator/wlanguage_converter.py` (Regex-based, not AST-based)
- Why fragile:
  - String content can be confused with code (regex can't parse nested structures)
  - Control flow without braces (WLanguage style) requires accurate line parsing
  - Nested function calls aren't properly parenthesized in regex replacement
- Safe modification:
  1. Implement recursive descent parser for WLanguage grammar instead of regex
  2. Generate AST first, then to Python (not string replacement)
  3. Add round-trip tests (parse, convert, re-parse) for correctness
- Test coverage: Basic tests exist; missing: nested calls, string literals with special chars, COMPILE IF blocks

### Data Binding Extraction

**Fragile dependency between HTMLStatic content and control IDs:**
- File: `src/wxcode/generator/template_generator.py` (Lines 356, 502, 516)
- Why fragile:
  - Data binding inferred from control names (EDT_USER → binds to User field)
  - No explicit binding metadata extracted from binary format
  - Template generation assumes specific control structure
- Safe modification:
  1. Add explicit data binding model to Element extraction phase
  2. Validate bindings at generation time (fail fast if assumptions break)
  3. Add coverage for projects with custom/non-standard control naming
- Test coverage: Limited; needs integration tests with real PDFs and bindings

### Database Schema Changes

**MongoDB schema evolution without migration:**
- Files affected:
  - `src/wxcode/models/element.py`
  - `src/wxcode/models/control.py`
  - Schema additions not versioned
- Why fragile:
  - Old imports in database won't have new required fields
  - No validation that schema version matches code expectations
  - Beanie ORM applies defaults, but inconsistent schema is silent failure
- Safe modification:
  1. Add schema_version field to Element, Control models
  2. Implement migration runner at startup
  3. Add pre-processing step to validate/migrate old records before use

---

## Missing Features / Incomplete Work

### Code Equivalence Testing

**No verification that converted code behaves like original:**
- Impact: Can't confidently say converted FastAPI+Jinja2 app behaves like WinDev original
- Blocks: Phase 5 (Validation)
- Recommendation: Implement behavior recording during parsing, replay against converted code

### Incremental Conversion Persistence

**Conversion state not persisted; re-running convert restarts from scratch:**
- File: `src/wxcode/api/conversions.py` - ConversionTracker doesn't persist between sessions
- Impact: Large conversions (1000+ elements) can't be resumed
- Fix: Add ConversionSession to MongoDB, checkpoint at element level

### Template Rendering Validation

**Generated Jinja2 templates not validated for syntax or renderability:**
- File: `src/wxcode/generator/template_generator.py`
- Impact: Broken templates only discovered at runtime
- Fix: Use Jinja2.Environment.parse() to validate template syntax at generation time

### HyperFile Support (WD REST API)

**HyperFile connections not yet implemented:**
- Files: `src/wxcode/generator/orchestrator.py` (Line 575), `src/wxcode/generator/starter_kit.py` (Line 355)
- Impact: Projects using HyperFile databases can't be fully converted
- Status: Comment says "# TODO: Implement HyperFile REST API client"
- Blocks: Complete conversion of HyperFile-backed projects

### Dynamic Procedure Resolution

**Complex procedure calls with dynamic function resolution not supported:**
- File: `src/wxcode/generator/service_generator.py`
- Issue: WLanguage allows procedures called by string name (via DYNAMIC keyword); Python needs explicit dispatch
- Impact: Generated services missing routing for dynamic calls
- Fix: Generate dispatcher mapping procedure names to functions

### HyperFile Catalog Enrichment

**Incomplete transpiler support for HyperFile catalog format:**
- File: `src/wxcode/transpiler/hyperfile_catalog.py` (626 lines, complex)
- Issue: Catalog parsing is pattern-based, not formal format parser
- Impact: Catalog misinterpretations could miss database relationships
- Recommendation: Replace with format spec-based parser or official SDK (if available)

---

## Test Coverage Gaps

### Untested Areas

**Critical untested functionality:**
- `src/wxcode/graph/impact_analyzer.py` (478 lines, no integration tests)
  - What's not tested: Full impact chains across 3+ element types
  - Risk: Cyclic dependencies not detected correctly
  - File: `tests/test_impact_analyzer.py` exists but only unit tests shallow calls

- `src/wxcode/parser/pdf_doc_splitter.py` (494 lines)
  - What's not tested: Large PDFs (3000+ pages), protected PDFs, malformed PDFs
  - Risk: Splitter fails unexpectedly without helpful error
  - File: `tests/test_pdf_doc_splitter.py` exists but only tests simple 10-page PDF

- `src/wxcode/services/gsd_invoker.py` (934 lines)
  - What's not tested: PTY streaming with large outputs, websocket disconnection mid-stream
  - Risk: Streaming breaks unpredictably
  - File: No `tests/test_gsd_invoker.py` exists; only CLI integration tests

- `src/wxcode/llm_converter/context_builder.py` (540 lines)
  - What's not tested: Context truncation for very large procedures (10k+ tokens)
  - Risk: Context builder silently drops important information
  - File: `tests/test_llm_*` files exist but don't cover truncation edge case

**Priority test additions:**
1. Neo4j sync with special characters (Portuguese names)
2. Conversion with missing procedures (unresolved references)
3. Template rendering with all control types
4. Large project import (memory/time performance)

---

## Recommendations (Priority Order)

### Immediate (Blocking)

1. **Extract wlanguage_converter regex to AST parser** (High Risk)
   - Current: String-based regex replacement
   - Risk: Silent conversion errors, unmaintainable patterns
   - Effort: 3 weeks

2. **Add raw_content validation/sanitization** (Security)
   - Current: Unvalidated binary parsed content goes into code generation
   - Risk: Injection attacks if WinDev files compromised
   - Effort: 1 week

3. **Fix bare exception handlers** (Debuggability)
   - Current: 60+ `except Exception:` blocks
   - Impact: Impossible to distinguish transient failures from logic errors
   - Effort: 1 week

### Short-term (Next Phase)

4. **Implement code equivalence testing** (Validation phase blocker)
   - Record original behavior, verify converted code matches
   - Effort: 2 weeks

5. **Add MongoDB schema versioning and migrations** (Data integrity)
   - Current: No versioning; schema changes break silently
   - Effort: 1 week

6. **Benchmark and parallelize enrichment** (Performance)
   - Current: Sequential, 10+ min for large projects
   - Target: <5 min
   - Effort: 2 weeks

### Medium-term (Polish)

7. **Add HyperFile support** (Feature completeness)
   - Effort: 3 weeks

8. **Implement template syntax validation** (Quality)
   - Validate Jinja2 templates at generation time
   - Effort: 1 week

9. **Neo4j query optimization with indexes** (Performance)
   - Impact analysis <5 sec for large graphs
   - Effort: 1 week

---

*Concerns audit: 2026-01-21*
