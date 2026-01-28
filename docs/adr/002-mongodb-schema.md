# ADR-002: MongoDB como Banco de Dados Intermediário

## Status

Aceito

## Contexto

Precisamos armazenar os elementos extraídos dos projetos WinDev de forma que:
- Suporte estruturas heterogêneas (páginas, classes, procedures, etc.)
- Permita armazenar AST/IR como documentos aninhados
- Facilite consultas por dependências
- Escale para projetos grandes

## Decisão

Escolhemos **MongoDB** como banco de dados intermediário.

### Schema Principal

```javascript
// Collection: elements
{
  _id: ObjectId,
  projectId: ObjectId,

  // Identificação
  sourceType: "page" | "procedure" | "class" | "query" | "report",
  sourceName: string,
  sourceFile: string,
  windevType: number,

  // Conteúdo
  rawContent: string,
  chunks: [
    { index: number, content: string, tokens: number, overlapStart?: number }
  ],

  // AST/IR (estrutura flexível)
  ast: {
    procedures: [...],
    variables: [...],
    controls: [...],
    events: [...],
    queries: [...]
  },

  // Grafo de Dependências
  dependencies: {
    uses: [string],        // Elementos que este usa
    usedBy: [string],      // Elementos que usam este
    dataFiles: [string],   // Tabelas acessadas
    externalAPIs: [string] // APIs externas chamadas
  },

  // Metadados de Conversão
  conversion: {
    status: "pending" | "in_progress" | "converted" | "validated" | "error",
    targetStack: string,
    targetFiles: [{ path: string, type: string }],
    convertedContent: object,
    issues: [string],
    humanReviewRequired: boolean
  },

  // Ordenação
  topologicalOrder: number,
  layer: "schema" | "domain" | "business" | "api" | "ui"
}
```

## Alternativas Consideradas

| Banco | Prós | Contras |
|-------|------|---------|
| PostgreSQL + JSONB | ACID, SQL | Menos flexível para docs aninhados |
| SQLite | Simples, sem servidor | Não escala, JSON limitado |
| Neo4j | Ótimo para grafos | Complexidade adicional |

## Consequências

### Positivas
- Schema flexível para diferentes tipos de elementos
- Fácil armazenar AST como documento
- Queries em dependências são naturais
- Motor (driver async) integra bem com FastAPI

### Negativas
- Requer MongoDB rodando
- Menos garantias ACID que PostgreSQL
- Precisa de índices bem planejados

## Índices Recomendados

```javascript
// Busca por projeto
db.elements.createIndex({ projectId: 1 })

// Busca por tipo e nome
db.elements.createIndex({ projectId: 1, sourceType: 1, sourceName: 1 })

// Busca por dependências
db.elements.createIndex({ "dependencies.uses": 1 })
db.elements.createIndex({ "dependencies.usedBy": 1 })

// Ordenação topológica
db.elements.createIndex({ projectId: 1, topologicalOrder: 1 })

// Status de conversão
db.elements.createIndex({ projectId: 1, "conversion.status": 1 })
```
