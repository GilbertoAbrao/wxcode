# Tasks: Add Neo4j Integration

## Overview
Implementar integração com Neo4j para análise avançada de grafos de dependências.

**Dependências externas:**
- Neo4j 5.x (Community Edition)
- neo4j Python driver

---

## Tasks

### 1. Setup e Configuração
- [x] Adicionar `neo4j` ao requirements.txt/pyproject.toml
- [x] Criar settings para Neo4j em `config.py` (uri, user, password, database)
- [x] Criar `src/wxcode/graph/__init__.py`
- [ ] Documentar instalação do Neo4j no README

**Validação:** `pip install -e .` passa sem erros

---

### 2. Neo4jConnection
- [x] Criar `src/wxcode/graph/neo4j_connection.py`
- [x] Implementar classe `Neo4jConnection` com:
  - `__init__(uri, user, password)`
  - `execute(query, parameters)` - executa query Cypher
  - `batch_create(items, query, batch_size)` - insere em lotes
  - `close()` - fecha conexão
- [x] Tratamento de erros (conexão recusada, auth inválida)
- [x] Context manager (`async with`)

**Validação:** Testes unitários com mock do driver

---

### 3. Neo4jSyncService
- [x] Criar `src/wxcode/graph/neo4j_sync.py`
- [x] Implementar `sync_project(project_id)`:
  - Limpar dados existentes do projeto
  - Criar nós :Table, :Class, :Procedure, :Page
  - Criar relacionamentos :INHERITS, :CALLS, :USES_TABLE, :USES_CLASS
- [x] Criar indexes após sync
- [x] Retornar `SyncResult` com contagens

**Validação:** Sync do Linkpay_ADM cria 493 nós e 1201 relacionamentos

---

### 4. Comando CLI sync-neo4j
- [x] Adicionar comando `sync-neo4j` ao CLI
- [x] Parâmetros: project_name, --clear, --validate, --dry-run
- [x] Exibir progresso e estatísticas
- [x] Tratar caso Neo4j não disponível

**Validação:** `wxcode sync-neo4j Linkpay_ADM` executa com sucesso

---

### 5. ImpactAnalyzer
- [x] Criar `src/wxcode/graph/impact_analyzer.py`
- [x] Implementar `get_impact(node_id, max_depth)`:
  - Query Cypher para encontrar todos dependentes
  - Retornar lista com nome, tipo, profundidade
- [x] Implementar `get_path(source, target)`:
  - Encontrar caminhos mais curtos entre dois nós
- [x] Implementar `find_hubs(min_connections)`:
  - Encontrar nós com muitas conexões

**Validação:** `get_impact("TABLE:CLIENTE")` retorna dependências corretas

---

### 6. Comando CLI impact
- [x] Adicionar comando `impact` ao CLI
- [x] Parâmetros: node_id, --depth, --format (table/json)
- [x] Output formatado com Rich

**Validação:** `wxcode impact TABLE:CLIENTE` lista elementos afetados

---

### 7. Comandos CLI Adicionais
- [x] Comando `path`: encontra caminhos entre nós
- [x] Comando `hubs`: lista nós com mais conexões
- [x] Comando `dead-code`: lista procedures não chamadas

**Validação:** Comandos executam e retornam dados corretos

---

### 8. Testes
- [x] Testes unitários para Neo4jConnection (mock)
- [x] Testes unitários para Neo4jSyncService (mock)
- [x] Testes unitários para ImpactAnalyzer (mock)
- [ ] Teste de integração com testcontainers-neo4j (opcional)

**Validação:** `pytest tests/test_neo4j*.py` passa

---

### 9. Documentação
- [x] Atualizar README com seção Neo4j
- [x] Atualizar CLAUDE.md com novos comandos
- [ ] Documentar queries Cypher úteis em `docs/neo4j-queries.md`

**Validação:** Documentação completa e precisa

---

## Ordem de Execução

```
1. Setup ──► 2. Connection ──► 3. SyncService ──► 4. CLI sync
                                      │
                                      ▼
                              5. ImpactAnalyzer ──► 6. CLI impact
                                      │
                                      ▼
                              7. CLI extras ──► 8. Testes ──► 9. Docs
```

**Tasks parallelizáveis:**
- Tasks 8 e 9 podem ser feitas em paralelo após task 7

## Estimativa
- Tasks 1-4: Fundação do sync
- Tasks 5-7: Análise de impacto
- Tasks 8-9: Qualidade e documentação
