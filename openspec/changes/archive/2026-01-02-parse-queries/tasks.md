# Tasks: Parse Queries

## Overview
Extrair SQL das queries do PDF de documentação e persistir no MongoDB.

**Fonte de dados:** PDF de documentação (Part 4 - Query)
**Marcador:** `SQL code of {QUERY_NAME}` seguido do SQL

---

## Task 1: Atualizar PDFDocumentSplitter para Queries
- [x] Adicionar `QUERY = "query"` ao enum `ElementType`
- [x] Adicionar padrão Part 4 ao `PART_PATTERNS`:
  - `"Part 4: Query": ElementType.QUERY`
  - `"Part 4 › Query": ElementType.QUERY`
- [x] Adicionar padrões de título para queries ao `ELEMENT_TITLE_PATTERNS`:
  - `r'^QRY_[A-Za-z0-9_]+$'`
  - `r'^Migration_[A-Za-z0-9_]+$'`
- [x] Criar pasta `queries/` no output do split-pdf
- [x] Atualizar `ProcessingStats` para incluir `queries_extracted`

**Arquivo:** `src/wxcode/parser/pdf_doc_splitter.py`

**Validação:** `wxcode split-pdf` extrai queries para `output/pdf_docs/queries/`

---

## Task 2: Criar QueryParser
- [x] Criar `src/wxcode/parser/query_parser.py`
- [x] Implementar `QueryParser` com método `parse(pdf_path: Path) -> QueryInfo`
- [x] Extrair SQL após marcador `SQL code of {NAME}`
- [x] Extrair parâmetros no formato `{ParamName}` do SQL
- [x] Extrair tabelas do SQL (FROM, JOIN)
- [x] Retornar estrutura:
  ```python
  @dataclass
  class QueryInfo:
      name: str
      sql: str
      parameters: list[str]  # ["ParamIDcliente", "ParamIDempresa"]
      tables: list[str]      # ["Cliente", "Empresa"]
  ```

**Validação:** Teste unitário parseia `QRY_PRODUTOS_ATIVOS.pdf` corretamente

---

## Task 3: Criar/Atualizar Modelo Query no MongoDB
- [x] Opção A: Reusar `Element` com `source_type="query"` e adicionar campos ao `ast`
- [ ] ~~Opção B: Criar modelo `Query` dedicado (similar a `Procedure`)~~ (Não usado)
- [x] Campos necessários adicionados ao ElementAST:
  - `sql: Optional[str]` (SQL completo)
  - `parameters: list[str]` (nome dos parâmetros)
  - `tables: list[str]` (tabelas referenciadas)
  - `incomplete: bool` (flag se SQL não encontrado)

**Arquivo:** `src/wxcode/models/element.py`

**Validação:** Schema MongoDB aceita documento query com todos os campos

---

## Task 4: Criar QueryEnricher
- [x] Criar `src/wxcode/parser/query_enricher.py`
- [x] Implementar `QueryEnricher`:
  - Busca elementos com `source_type="query"` no MongoDB
  - Para cada query, busca PDF correspondente em `queries/{name}.pdf`
  - Usa `QueryParser` para extrair SQL
  - Atualiza documento no MongoDB
- [x] Tratar casos:
  - Query sem PDF correspondente → log warning
  - PDF sem SQL → marcar `ast.incomplete = true`

**Validação:** `QueryEnricher` atualiza elementos query no MongoDB

---

## Task 5: Integrar ao CLI
- [x] Atualizar comando `enrich` para incluir queries:
  - Após enriquecer pages/windows, enriquecer queries
  - Integrado diretamente ao comando `enrich` existente
- [x] Exibir estatísticas de queries enriquecidas

**Arquivo:** `src/wxcode/cli.py`

**Validação:** `wxcode enrich ./projeto --pdf-docs ./output/pdf_docs` processa queries

---

## Task 6: Testes
- [x] Teste unitário: `QueryParser.parse()` extrai SQL e parâmetros
- [x] Teste unitário: `QueryParser` extrai tabelas de FROM/JOIN
- [x] Teste unitário: `QueryParser._extract_sql()` com marcadores e seções
- [x] Testes criados em `tests/test_query_parser.py`

**Arquivo:** `tests/test_query_parser.py`

**Validação:** `pytest tests/test_query_parser.py` passa

---

## Ordem de Execução

```
Task 1 (PDFSplitter) ──► Task 2 (QueryParser) ──► Task 3 (Model)
                                                      │
                                                      ▼
                              Task 4 (Enricher) ──► Task 5 (CLI) ──► Task 6 (Tests)
```

**Tasks parallelizáveis:**
- Task 2 e Task 3 podem ser feitas em paralelo após Task 1
- Task 6 pode começar junto com Task 4

---

## Dados de Referência

**Exemplo de SQL no PDF:**
```
SQL code of QRY_PRODUTOS_ATIVOS
SELECT
EmpresaProdutos.IDEmpresaProduto AS IDEmpresaProduto,
EmpresaProdutos.IDempresa AS IDempresa,
EmpresaProdutos.DescricaoProduto AS DescricaoProduto,
EmpresaProdutos.ValorProduto AS ValorProduto,
EmpresaProdutos.Inativo AS Inativo
FROM
EmpresaProdutos
WHERE
EmpresaProdutos.Inativo = 0
AND EmpresaProdutos.IDempresa = 677
ORDER BY
DescricaoProduto ASC
```

**Exemplo com parâmetros:**
```
SQL code of QRY_PRODUTO_CLIENTE
SELECT
ClienteProduto.IDClienteProduto AS IDClienteProduto,
ClienteProduto.IDcliente AS IDcliente
FROM
ClienteProduto
WHERE
ClienteProduto.IDEmpresaProduto = {ParamIDEmpresaProduto}
AND ClienteProduto.IDcliente = {ParamIDcliente}
```
