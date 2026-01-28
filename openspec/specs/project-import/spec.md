# project-import Specification

## Purpose
TBD - created by archiving change populate-raw-content-on-import. Update Purpose after archive.
## Requirements
### Requirement: Element creation during import
O sistema MUST popular o campo `raw_content` de cada elemento durante o import inicial.

#### Scenario: Import element with existing source file
- **Given** um elemento com `source_file` apontando para arquivo existente
- **When** `ProjectMapper._create_element()` é executado
- **Then** o campo `raw_content` MUST conter o conteúdo do arquivo
- **And** o conteúdo MUST ser lido com encoding UTF-8 e `errors='replace'`

#### Scenario: Import element with missing source file
- **Given** um elemento com `source_file` apontando para arquivo inexistente
- **When** `ProjectMapper._create_element()` é executado
- **Then** o campo `raw_content` MUST ser string vazia
- **And** nenhum erro MUST ser lançado

#### Scenario: Import element with read error
- **Given** um elemento com `source_file` que causa erro de leitura
- **When** `ProjectMapper._create_element()` é executado
- **Then** o campo `raw_content` MUST ser string vazia
- **And** um warning MUST ser logado
- **And** o import MUST continuar normalmente

### Requirement: Source file reading
O sistema MUST prover método `_read_source_file()` para leitura robusta de arquivos fonte.

#### Scenario: Read existing file
- **Given** um arquivo fonte existente no disco
- **When** `_read_source_file(file_path)` é chamado
- **Then** o conteúdo completo MUST ser retornado como string
- **And** encoding UTF-8 MUST ser usado
- **And** caracteres inválidos MUST ser substituídos (não causar exceção)

#### Scenario: Read non-existent file
- **Given** um caminho para arquivo que não existe
- **When** `_read_source_file(file_path)` é chamado
- **Then** string vazia MUST ser retornada
- **And** nenhuma exceção MUST ser lançada

#### Scenario: Handle read exceptions
- **Given** um arquivo que causa exceção ao ser lido
- **When** `_read_source_file(file_path)` é chamado
- **Then** string vazia MUST ser retornada
- **And** exceção MUST ser capturada
- **And** warning MUST ser logado com caminho e erro

### Requirement: MongoDB consistency
Após import completo, MongoDB MUST ser fonte única da verdade para `raw_content`.

#### Scenario: Query element after import
- **Given** um projeto foi importado com sucesso
- **When** query em `Element.find()` é executada
- **Then** todos elementos com arquivo fonte válido MUST ter `raw_content` populado
- **And** elementos sem arquivo fonte MUST ter `raw_content=""` (não NULL/undefined)

#### Scenario: API returns element data
- **Given** um elemento no MongoDB após import
- **When** API endpoint `/api/elements/{id}` é chamado
- **Then** `raw_content` retornado MUST ser o mesmo armazenado no MongoDB
- **And** nenhuma leitura de disco MUST ocorrer (dados já estão no banco)

