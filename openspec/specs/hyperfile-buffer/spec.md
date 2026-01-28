# hyperfile-buffer Specification

## Purpose
TBD - created by archiving change add-wlanguage-context-awareness. Update Purpose after archive.
## Requirements
### Requirement: HFBUF-DOC-001 - Documentação de Buffer Global

O sistema MUST ter documentação explicando o modelo de buffer global do HyperFile.

#### Scenario: Documento existe

**Given** o diretório docs/wlanguage/
**When** verifico os arquivos
**Then** deve existir `hyperfile-buffer.md`

#### Scenario: Conteúdo do documento

**Given** o arquivo docs/wlanguage/hyperfile-buffer.md
**When** leio o conteúdo
**Then** deve conter:
- Explicação do conceito de buffer global
- Diagrama de arquitetura
- Exemplos de conflito de buffer
- Padrões de conversão para Python

---

### Requirement: HFBUF-PATTERNS-001 - Padrões de Conversão Documentados

A documentação MUST incluir padrões de conversão HyperFile → Python.

#### Scenario: Padrão Loop HReadFirst/HReadNext

**Given** código WLanguage com HReadFirst/HReadNext loop
**When** consulto a documentação
**Then** deve mostrar conversão para `async for` com cursor MongoDB

#### Scenario: Padrão HReset + HAdd

**Given** código WLanguage com HReset + atribuições + HAdd
**When** consulto a documentação
**Then** deve mostrar conversão para `insert_one(dict)`

#### Scenario: Padrão FileToScreen

**Given** código WLanguage com FileToScreen()
**When** consulto a documentação
**Then** deve mostrar conversão para template context em Jinja2

#### Scenario: Padrão ScreenToFile

**Given** código WLanguage com ScreenToFile()
**When** consulto a documentação
**Then** deve mostrar conversão para form data extraction em FastAPI

---

### Requirement: HFBUF-TRACK-001 - Rastreamento de Uso de Tabelas via Binding

O dependency extractor MUST rastrear tabelas usadas via binding.

#### Scenario: Tabela extraída de binding

**Given** um controle com data_binding.table_name = "CLIENTE"
**When** o dependency extractor processa os controles
**Then** a lista de dependências deve incluir TableUsage com:
- `table_name = "CLIENTE"`
- `usage_type = "binding"`
- `context = "control:EDT_Nome"`

#### Scenario: Múltiplas tabelas via binding

**Given** controles com binding para CLIENTE, PRODUTO e PEDIDO
**When** o dependency extractor processa os controles
**Then** todas as três tabelas devem estar nas dependências

#### Scenario: Tabela duplicada

**Given** dois controles com binding para CLIENTE.nome e CLIENTE.cpf
**When** o dependency extractor processa os controles
**Then** CLIENTE deve aparecer apenas uma vez na lista de tabelas únicas

