# Proposal: Add Neo4j Integration

## Change ID
`add-neo4j-integration`

## Summary
Adicionar Neo4j como banco de grafos opcional para análise avançada de dependências, incluindo análise de impacto, detecção de padrões e visualização interativa.

## Motivation

### Problema
O MongoDB armazena as dependências como arrays dentro de cada documento. Isso é suficiente para a conversão básica (seguir ordem topológica), mas limita análises avançadas:

- **Análise de impacto**: "Se eu mudar a tabela CLIENTE, quais páginas são afetadas?" requer múltiplos lookups recursivos
- **Detecção de padrões**: Identificar "hubs" críticos, comunidades de código, código morto
- **Queries de caminho**: "Qual o caminho de PAGE_Login até USUARIO?" é complexo em MongoDB

### Solução
Neo4j é um banco de grafos nativo que oferece:
- **Cypher**: Linguagem declarativa para queries de grafo
- **Traversal nativo**: Seguir relacionamentos é O(1) por hop
- **Algoritmos built-in**: PageRank, community detection, shortest path
- **Visualização**: Neo4j Browser e Bloom para exploração interativa

### Abordagem
MongoDB permanece como source of truth. Neo4j é sincronizado on-demand para análise avançada:

```
MongoDB (source of truth)
    │
    ├──► Conversão (Fase 4) ──► Código Python
    │
    └──► Neo4j (sync on-demand) ──► Análise/Visualização
```

## Scope

### In Scope
1. Comando CLI `wxcode sync-neo4j` para sincronizar grafo
2. Comando CLI `wxcode impact <node>` para análise de impacto
3. Modelo de dados Neo4j (labels, relationships)
4. Conexão configurável via settings
5. Queries Cypher para casos de uso comuns

### Out of Scope
- Migração completa para Neo4j (MongoDB continua como principal)
- Interface web para visualização (usar Neo4j Browser)
- Escrita de volta para MongoDB via Neo4j
- Sincronização automática/real-time

## Success Criteria
1. `sync-neo4j` exporta 100% dos nós e arestas do projeto Linkpay_ADM
2. `impact TABLE:CLIENTE` retorna todas as dependências em < 1 segundo
3. Neo4j Browser visualiza o grafo completo
4. Testes cobrem sync e queries principais

## Dependencies
- Neo4j 5.x (Community Edition é suficiente)
- neo4j Python driver
- Spec existente: `dependency-analysis`

## Risks and Mitigations

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Neo4j não instalado | Média | Baixo | Comando falha graciosamente com instrução de instalação |
| Sincronização lenta para grafos grandes | Baixa | Médio | Usar batch transactions |
| Modelo de dados inconsistente | Baixa | Alto | Validar contagem de nós/arestas após sync |

## Alternatives Considered

| Alternativa | Prós | Contras | Decisão |
|-------------|------|---------|---------|
| Apenas MongoDB | Simples, sem nova dependência | Queries de grafo verbosas | ❌ Não atende análise avançada |
| NetworkX persistido | Python nativo | Não escala, sem visualização | ❌ Limitado |
| ArangoDB | Multi-model (doc + graph) | Menos popular, menos tooling | ❌ Neo4j tem melhor ecossistema |
| **Neo4j** | Cypher poderoso, visualização nativa | Nova dependência | ✅ Melhor fit para grafos |

## References
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- Spec relacionada: `openspec/specs/dependency-analysis/spec.md`
