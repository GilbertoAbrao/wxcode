# procedure-parsing Specification

## Purpose
TBD - created by archiving change add-procedure-parser. Update Purpose after archive.
## Requirements
### Requirement: Parse WDG Files
The system SHALL parse .wdg files (WinDev procedure groups) and extract individual procedures with their metadata.

#### Scenario: Parse simple procedure file
- **GIVEN** a .wdg file with one procedure
- **WHEN** the parser processes the file
- **THEN** the procedure name, parameters, return type, and code are extracted
- **AND** a Procedure document is created in MongoDB

#### Scenario: Parse file with multiple procedures
- **GIVEN** a .wdg file with 5 procedures
- **WHEN** the parser processes the file
- **THEN** 5 Procedure documents are created
- **AND** each procedure references the parent Element

#### Scenario: Handle empty procedure file
- **GIVEN** a .wdg file with no procedures
- **WHEN** the parser processes the file
- **THEN** no Procedure documents are created
- **AND** no error is raised

---

### Requirement: Extract Procedure Signature
The system SHALL extract the complete signature of each procedure including name, parameters with types, and return type.

#### Scenario: Procedure with typed parameters
- **GIVEN** a procedure `PROCEDURE BuscaCEP(sCEP is string): JSON`
- **WHEN** parsed
- **THEN** name = "BuscaCEP"
- **AND** parameters = [{name: "sCEP", type: "string"}]
- **AND** return_type = "JSON"

#### Scenario: Procedure without return type
- **GIVEN** a procedure `PROCEDURE ProcessarDados(nId is int)`
- **WHEN** parsed
- **THEN** return_type = None

#### Scenario: Procedure with multiple parameters
- **GIVEN** a procedure `PROCEDURE Calcular(a is int, b is real, c is string): real`
- **WHEN** parsed
- **THEN** parameters has 3 items with correct names and types

---

### Requirement: Extract Procedure Dependencies
The system SHALL analyze procedure code to identify dependencies on other procedures, HyperFile operations, and external APIs.

#### Scenario: Detect procedure calls
- **GIVEN** a procedure that calls `ValidarCPF()` and `FormatarData()`
- **WHEN** parsed
- **THEN** calls_procedures = ["ValidarCPF", "FormatarData"]

#### Scenario: Detect HyperFile operations
- **GIVEN** a procedure using `HReadFirst(CLIENTE)` and `HAdd(PEDIDO)`
- **WHEN** parsed
- **THEN** uses_files = ["CLIENTE", "PEDIDO"]

#### Scenario: Detect REST API calls
- **GIVEN** a procedure using `RESTSend(cMyRequest)`
- **WHEN** parsed
- **THEN** uses_apis includes "REST"

---

### Requirement: CLI Command for Procedure Parsing
The system SHALL provide a CLI command to parse procedures from .wdg files.

#### Scenario: Parse all procedures in project
- **GIVEN** a project with 10 .wdg files imported
- **WHEN** user runs `wxcode parse-procedures --project Linkpay_ADM`
- **THEN** all .wdg files are parsed
- **AND** procedures are stored in MongoDB
- **AND** summary is displayed (X procedures found in Y files)

#### Scenario: Parse specific file
- **GIVEN** a specific .wdg file path
- **WHEN** user runs `wxcode parse-procedures --file ./Util.wdg`
- **THEN** only that file is parsed

---

### Requirement: Store Procedures in MongoDB
The system SHALL store parsed procedures in a `procedures` collection with references to parent elements.

#### Scenario: Procedure document structure
- **GIVEN** a parsed procedure
- **WHEN** stored in MongoDB
- **THEN** document contains: element_id, project_id, name, parameters, return_type, code, dependencies

#### Scenario: Query procedures by element
- **GIVEN** an Element document for "Util.wdg"
- **WHEN** querying procedures by element_id
- **THEN** all procedures from that file are returned

