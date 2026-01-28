# Handoff: Integração da Knowledge Base com Workflow GSD

**Data**: 2025-01-22
**Origem**: Conversa no projeto Linkpay_ADM
**Objetivo**: Implementar MCP Server para integrar KB (MongoDB + Neo4j) no workflow de conversão Windev/Webdev

---

## Contexto

O usuário possui uma **Knowledge Base já construída** com:

1. **MongoDB**: Codebase Windev/Webdev "explodida" - definições de telas, código, regras de negócio
2. **Neo4j**: Grafo de dependências entre telas/componentes com ordem topológica
3. **Granularidade**: Nível de controle de tela

Esta KB representa o trabalho de engenharia reversa do sistema legado e é o ativo principal para guiar a conversão de stack.

---

## Diferença entre Comandos GSD (Referência)

### `/gsd:new-milestone`
- **Escopo**: Ciclo completo de trabalho com múltiplas fases
- **Uso**: Iniciar um novo objetivo macro (ex: "Converter módulo de pagamentos para React")
- **Produz**: `PROJECT.md` atualizado + roadmap com várias fases
- **Quando usar**: Início de um esforço significativo que precisa ser quebrado em etapas

### `/gsd:plan-phase`
- **Escopo**: Uma única fase dentro de um milestone
- **Uso**: Planejar a execução detalhada de uma fase específica
- **Produz**: `PLAN.md` com tarefas, dependências e verificação
- **Quando usar**: Quando já existe um roadmap e você quer executar uma fase

### Hierarquia GSD
```
Projeto
└── Milestone (objetivo macro)
    ├── Phase 1 → PLAN.md → Execução
    ├── Phase 2 → PLAN.md → Execução
    └── Phase N → PLAN.md → Execução
```

---

## Decisão de Arquitetura: MCP Server

### Por que MCP Server?

- Integração nativa com Claude Code e workflow GSD
- Consultas dinâmicas durante planejamento e execução
- Permite que os agentes GSD consultem a KB automaticamente

### Tools Propostos para o MCP Server

| Tool | Descrição | Fonte |
|------|-----------|-------|
| `get_screen_definition` | Retorna definição completa de uma tela (código, controles, eventos) | MongoDB |
| `get_dependencies` | Lista dependências de uma tela/componente | Neo4j |
| `get_topological_order` | Ordem de conversão sugerida para um conjunto de telas | Neo4j |
| `get_conversion_candidates` | Próximas telas prontas para converter (deps já convertidas) | Neo4j |
| `search_code_patterns` | Busca padrões específicos no código legado | MongoDB |
| `get_data_model` | Schema/entidades relacionadas a uma tela | MongoDB |
| `mark_as_converted` | Marca uma tela como convertida no grafo | Neo4j |
| `get_module_screens` | Lista todas as telas de um módulo funcional | MongoDB |

### Arquitetura

```
┌─────────────────┐     ┌─────────────────┐
│   Claude Code   │────▶│  MCP Server     │
│   (GSD workflow)│◀────│  (windev-kb)    │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
              ┌──────────┐              ┌──────────┐
              │ MongoDB  │              │  Neo4j   │
              │ (telas,  │              │ (grafo   │
              │ código)  │              │ depend.) │
              └──────────┘              └──────────┘
```

### Fluxo de Integração com GSD

```
┌─────────────────────────────────────────────────────────────┐
│                    /gsd:new-milestone                        │
│  "Converter Módulo X"                                        │
│                                                              │
│  1. Consulta KB: quais telas pertencem ao módulo?           │
│  2. Consulta Neo4j: ordem topológica dessas telas           │
│  3. Gera phases automaticamente baseado na ordem            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    /gsd:plan-phase                           │
│  "Converter SCR_LOGIN"                                       │
│                                                              │
│  1. Consulta KB: definição completa da tela                 │
│  2. Consulta KB: dependências (procedures, queries, etc)    │
│  3. Gera PLAN.md com mapeamento Windev → Nova Stack         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    /gsd:execute-phase                        │
│                                                              │
│  Durante execução, consulta KB para:                        │
│  - Código original da tela                                  │
│  - Regras de negócio embarcadas                            │
│  - Validações e tratamentos de erro                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Esqueleto do MCP Server

```typescript
// mcp-windev-kb/src/index.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { MongoClient } from "mongodb";
import neo4j from "neo4j-driver";

const server = new Server({
  name: "windev-kb",
  version: "1.0.0",
});

// Tool: Obter próximas telas convertíveis (sem dependências pendentes)
server.setRequestHandler("tools/call", async (request) => {
  if (request.params.name === "get_conversion_candidates") {
    const result = await neo4jSession.run(`
      MATCH (s:Screen)
      WHERE NOT EXISTS {
        MATCH (s)-[:DEPENDS_ON]->(dep:Screen)
        WHERE dep.converted = false
      }
      AND s.converted = false
      RETURN s.id, s.name, s.complexity
      ORDER BY s.complexity ASC
      LIMIT 10
    `);
    return { candidates: result.records };
  }

  if (request.params.name === "get_screen_definition") {
    const screen = await mongodb
      .collection("screens")
      .findOne({ id: request.params.arguments.screen_id });
    return screen;
  }

  if (request.params.name === "get_topological_order") {
    const result = await neo4jSession.run(`
      MATCH (s:Screen)
      WHERE s.module = $module AND s.converted = false
      WITH s
      MATCH path = (s)-[:DEPENDS_ON*0..]->(dep)
      WITH s, max(length(path)) as depth
      RETURN s.id, s.name, depth
      ORDER BY depth ASC
    `, { module: request.params.arguments.module });
    return { order: result.records };
  }

  if (request.params.name === "mark_as_converted") {
    await neo4jSession.run(`
      MATCH (s:Screen {id: $screenId})
      SET s.converted = true, s.convertedAt = datetime()
    `, { screenId: request.params.arguments.screen_id });
    return { success: true };
  }
});
```

---

## Workflow Recomendado para Conversão

### Para uma codebase preexistente com KB já construída:

1. **`/gsd:map-codebase`** (opcional se KB já tem tudo)
   - Pode ser pulado se a KB já documenta a estrutura

2. **`/gsd:new-milestone`** por módulo funcional
   - Ex: "Converter Módulo de Autenticação"
   - Ex: "Converter Módulo de Pagamentos"
   - NÃO fazer por camada técnica (ex: "migrar todo banco")

3. **Para cada phase do milestone:**
   ```
   /gsd:plan-phase    # Planeja usando dados da KB
   /gsd:execute-phase # Executa com consultas à KB
   /gsd:verify-work   # Valida resultado
   ```

4. **`/gsd:complete-milestone`** ao finalizar módulo

---

## Próximos Passos (TODO)

1. [ ] **Definir estrutura dos documentos MongoDB**
   - Qual o schema atual das telas?
   - Quais campos são relevantes para conversão?

2. [ ] **Mapear queries Cypher existentes**
   - Query de ordem topológica
   - Query de dependências
   - Estrutura dos nodes e relationships

3. [ ] **Criar projeto do MCP Server**
   - Setup TypeScript + MCP SDK
   - Conexões MongoDB e Neo4j
   - Implementar tools básicos

4. [ ] **Configurar no Claude Code**
   - Adicionar ao `.mcp.json` do projeto
   - Testar integração

5. [ ] **Integrar com workflow GSD**
   - Customizar prompts das phases para usar os tools
   - Criar templates de milestone para conversão

---

## Perguntas para Continuar

1. **Estrutura MongoDB**: Como está estruturado um documento de tela? (exemplo de JSON)
2. **Schema Neo4j**: Quais são os labels de nodes e tipos de relationships?
3. **APIs existentes**: Já existe alguma API REST/GraphQL para consultar a KB?
4. **Localização**: Onde estão rodando MongoDB e Neo4j? (local, cloud, docker)

---

## Referências

- Projeto origem da conversa: `/Users/gilberto/projetos/wxk/test-gsd-windev/Linkpay_ADM`
- Este projeto: `/Users/gilberto/projetos/wxk/wxcode`
- Documentação MCP SDK: https://modelcontextprotocol.io/
