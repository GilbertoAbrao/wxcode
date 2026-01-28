# Proposal: Parse Queries

## Change ID
`parse-queries`

## Summary
Implementar parsing de queries (.WDR) extraindo SQL e parâmetros do PDF de documentação, seguindo o mesmo padrão usado para pages/windows.

## Motivation

### Problema
- 102 queries existem no MongoDB mas com `raw_content` vazio e `ast` null
- Arquivos `.WDR` são **binários** (não há formato texto)
- Sem o SQL das queries, conversão não consegue gerar SQLAlchemy queries

### Solução
O PDF de documentação contém o SQL completo das queries na **Part 4**:
- Marcador: `SQL code of {QUERY_NAME}` seguido do SQL
- Contém SQL completo com parâmetros `{ParamName}`
- Mesma estrutura já usada para pages/windows

### Abordagem
1. Estender `PDFDocumentSplitter` para extrair queries (Part 4)
2. Criar `QueryParser` para parsear SQL e extrair parâmetros
3. Criar modelo `Query` no MongoDB (ou reusar Element)
4. Integrar ao comando `enrich`

## Scope

### In Scope
1. Atualizar `PDFDocumentSplitter` para reconhecer Part 4 (Query)
2. Criar parser de SQL que extrai:
   - Nome da query
   - SQL completo (após marcador `SQL code of {NAME}`)
   - Parâmetros (formato `{ParamName}`)
   - Tabelas referenciadas (FROM/JOIN)
3. Persistir no MongoDB
4. Atualizar comando `split-pdf` e `enrich`

### Out of Scope
- Parsing de arquivos `.WDR` binários (usar apenas PDF)
- Conversão de queries para SQLAlchemy (fase 4)
- Validação de sintaxe SQL

## Success Criteria
1. `split-pdf` extrai queries para pasta `queries/`
2. `enrich` popula `raw_content` e `ast` dos 102 elementos query
3. Cada query tem SQL e lista de parâmetros
4. Tabelas referenciadas são extraídas para dependências

## Dependencies
- PDFDocumentSplitter existente
- Spec: `page-code-parsing` (padrão similar)

## Risks and Mitigations

| Risco | Mitigação |
|-------|-----------|
| Algumas queries sem SQL no PDF | Log warning, marcar como incomplete |
| SQL com sintaxe WinDev específica | Extrair raw, normalizar na conversão |
| Parâmetros com tipos não documentados | Inferir tipo do contexto ou marcar como unknown |
