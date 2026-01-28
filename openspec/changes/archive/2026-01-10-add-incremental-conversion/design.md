# Design: add-incremental-conversion

## Context

O wxcode converte projetos WinDev/WebDev para FastAPI + Jinja2 usando LLM. Atualmente, cada conversão é independente - o LLM gera código sem acumular conhecimento das conversões anteriores.

## Problem Statement

1. **Sem contexto acumulado**: Cada conversão é isolada
2. **Decisões não documentadas**: Por que mapear EDT_Login para `<input type="text">`?
3. **Inconsistência**: Elementos similares podem ser convertidos diferentemente
4. **Sem histórico**: Não há registro de como elementos foram convertidos

## Proposed Solution

### Arquitetura: Conversão Incremental via OpenSpec

```
┌─────────────────────────────────────────────────────────────────┐
│                    MongoDB (Source of Truth)                     │
│  Elements com: topological_order, layer, conversion.status       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ConversionTracker                             │
│  - get_next_pending(project) → Element                          │
│  - mark_status(element_id, status)                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SpecContextLoader                             │
│  - load_dependency_specs(element) → list[str]                   │
│  - Busca em openspec/specs/{dep}-spec/spec.md                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ProposalGenerator                             │
│  - generate(element, dep_specs) → ProposalOutput                │
│  - Usa LLM com prompt específico                                │
│  - Gera: proposal.md, tasks.md, spec.md                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OpenSpec Integration                          │
│  - openspec validate {element}-spec                             │
│  - openspec apply {element}-spec (após revisão)                 │
│  - openspec archive {element}-spec                              │
└─────────────────────────────────────────────────────────────────┘
```

## Design Decisions

### DD-1: Nomenclatura de Specs

**Decisão:** Usar formato `{element}-spec` (ex: `page-login-spec`, `class-usuario-spec`)

**Alternativas consideradas:**
- `convert-{element}`: Ambíguo, não indica que é spec
- `{element}-conversion`: Longo demais
- `{type}/{element}`: Hierarquia desnecessária

**Rationale:** Consistente com specs existentes (`schema-generator`, `service-generator`), claramente identificável como spec de conversão.

### DD-2: Localização das Specs

**Decisão:** `openspec/specs/` (junto com specs existentes)

**Alternativas consideradas:**
- `openspec/conversions/`: Separado, mas fragmenta a base de conhecimento
- `output/specs/`: Mistura geração com fonte de verdade

**Rationale:** Specs de conversão são specs como qualquer outra. O prefixo `{element}-spec` distingue das specs de funcionalidade.

### DD-3: Granularidade

**Decisão:** Uma spec por elemento

**Alternativas consideradas:**
- Uma spec por camada (schema, domain, etc.): Perde contexto específico
- Uma spec por grupo de elementos: Difícil de referenciar

**Rationale:** Cada elemento tem suas decisões de mapeamento. Specs individuais permitem referência precisa.

### DD-4: Workflow Semi-automático

**Decisão:** CLI gera proposal, humano revisa, apply/archive automáticos

**Alternativas consideradas:**
- Totalmente automático: Perde oportunidade de correção
- Totalmente manual: Muito lento

**Rationale:** Humano pode intervir nos pontos críticos (revisão da proposal) sem overhead em operações mecânicas.

### DD-5: Status de Conversão

**Decisão:** Campo `conversion.status` no MongoDB com valores: `pending`, `proposal_generated`, `converted`, `archived`

**Alternativas consideradas:**
- Arquivo separado de tracking: Sincronização complexa
- Flags booleanas: Não captura estados intermediários

**Rationale:** Estado vive junto com o elemento, fácil de consultar e atualizar.

## Integration Points

### MongoDB
- Leitura: `Element.find({"conversion.status": "pending"}).sort("topological_order")`
- Escrita: `Element.update_one({"_id": id}, {"$set": {"conversion.status": status}})`

### OpenSpec CLI
- `openspec validate {id}`: Valida proposal gerada
- `openspec apply {id}`: Implementa código
- `openspec archive {id}`: Move para specs/

### LLM Provider
- Reutiliza infraestrutura existente (`create_provider()`)
- Novo prompt em `prompts.py` para geração de proposals

## Risks and Mitigations

| Risco | Mitigação |
|-------|-----------|
| LLM gera spec inválida | Validação automática + retry |
| Proposals muito grandes | Limitar escopo por elemento |
| Dependência circular | Ordem topológica já resolvida no grafo |
| OpenSpec CLI falha | Capturar erro, reverter status |

## Future Considerations

1. **Batch mode**: Converter múltiplos elementos sem pausa
2. **Diff mode**: Mostrar diferença entre spec esperada e gerada
3. **Learning mode**: LLM aprende padrões das specs arquivadas
4. **Rollback**: Reverter conversão se spec aplicada tiver problemas
