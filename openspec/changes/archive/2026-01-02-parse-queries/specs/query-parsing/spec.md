# query-parsing Specification

## Purpose
Extrair SQL e parâmetros de queries do PDF de documentação WebDev, persistindo no MongoDB para uso na conversão.

## ADDED Requirements

### Requirement: Extract Queries from PDF
O sistema MUST extrair queries da Part 4 do PDF de documentação.

#### Scenario: Split PDF extrai queries
- Given PDF de documentação com Part 4 contendo queries
- When `wxcode split-pdf` executa
- Then pasta `queries/` é criada no output
- And cada query gera um PDF individual

#### Scenario: Reconhece padrão Part 4
- Given página com texto "Part 4 › Query"
- When PDFDocumentSplitter processa
- Then identifica como seção de queries

#### Scenario: Identifica nome da query
- Given página com "SQL code of QRY_PRODUTOS_ATIVOS"
- When QueryParser processa
- Then extrai nome "QRY_PRODUTOS_ATIVOS"

---

### Requirement: Parse SQL Content
O sistema MUST extrair SQL completo após o marcador `SQL code of {NAME}`.

#### Scenario: Extrai SQL simples
- Given página com SQL após marcador
- When QueryParser.parse() executa
- Then `QueryInfo.sql` contém SQL completo

#### Scenario: SQL multilinha preservado
- Given SQL com SELECT, FROM, WHERE em linhas separadas
- When parseado
- Then quebras de linha são preservadas

#### Scenario: SQL com ORDER BY
- Given SQL terminando com ORDER BY
- When parseado
- Then ORDER BY é incluído no SQL extraído

---

### Requirement: Extract Parameters
O sistema MUST extrair parâmetros no formato `{ParamName}`.

#### Scenario: Query com parâmetros
- Given SQL com `WHERE campo = {ParamIDcliente}`
- When QueryParser extrai parâmetros
- Then `parameters` contém "ParamIDcliente"

#### Scenario: Múltiplos parâmetros
- Given SQL com `{ParamA}` e `{ParamB}`
- When parseado
- Then `parameters` contém ["ParamA", "ParamB"]

#### Scenario: Query sem parâmetros
- Given SQL sem `{...}`
- When parseado
- Then `parameters` é lista vazia

#### Scenario: Mesmo parâmetro usado múltiplas vezes
- Given SQL com `{ParamID}` aparecendo 2 vezes
- When parseado
- Then `parameters` contém "ParamID" apenas uma vez

---

### Requirement: Extract Referenced Tables
O sistema MUST extrair tabelas referenciadas no SQL.

#### Scenario: Tabela no FROM
- Given SQL com `FROM EmpresaProdutos`
- When QueryParser extrai tabelas
- Then `tables` contém "EmpresaProdutos"

#### Scenario: Múltiplas tabelas com JOIN
- Given SQL com `FROM A JOIN B ON ...`
- When parseado
- Then `tables` contém ["A", "B"]

#### Scenario: Tabela com alias
- Given SQL com `FROM Cliente c`
- When parseado
- Then `tables` contém "Cliente"

---

### Requirement: Persist to MongoDB
O sistema MUST persistir informações da query no MongoDB.

#### Scenario: Enrich atualiza elemento query
- Given elemento com `source_type="query"` no MongoDB
- And PDF correspondente em `queries/{name}.pdf`
- When QueryEnricher executa
- Then `raw_content` é atualizado com SQL
- And `ast.parameters` contém lista de parâmetros
- And `dependencies.uses_tables` contém tabelas

#### Scenario: Query sem PDF
- Given elemento query sem PDF correspondente
- When QueryEnricher executa
- Then warning é logado
- And elemento não é modificado

---

### Requirement: CLI Integration
O sistema MUST integrar parsing de queries ao comando enrich.

#### Scenario: Enrich processa queries
- Given projeto com queries no MongoDB
- And PDFs de queries em `pdf_docs/queries/`
- When `wxcode enrich ./projeto --pdf-docs ./pdf_docs`
- Then queries são enriquecidas junto com pages/windows

#### Scenario: Estatísticas incluem queries
- Given enrich completo
- When estatísticas exibidas
- Then mostra "Queries enriched: X"

---

## Cross-References
- Depende de: `page-code-parsing` (padrão similar de enriquecimento)
- Usado por: `dependency-analysis` (tabelas como dependências)
