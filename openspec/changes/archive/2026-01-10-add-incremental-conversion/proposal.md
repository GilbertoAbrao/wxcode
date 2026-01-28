# Proposal: add-incremental-conversion

## Summary

Implementar conversão incremental via OpenSpec, onde cada elemento convertido vira uma proposal que documenta as decisões de mapeamento e serve de referência para os próximos elementos.

## Problem

Atualmente o conversor LLM:
- Gera código diretamente sem acumular conhecimento
- Cada conversão é independente, sem contexto das anteriores
- Decisões de mapeamento não são documentadas
- Não há histórico de como elementos foram convertidos
- Dificuldade em manter consistência entre conversões similares

## Solution

Criar um fluxo de conversão incremental que:
1. Segue a ordem topológica (schema → domain → business → api → ui)
2. Para cada elemento, gera uma proposal OpenSpec via LLM
3. A proposal inclui specs que documentam os mapeamentos
4. Após archive, a spec fica disponível como referência
5. Próximos elementos consultam specs das dependências

```
Elemento → LLM + specs deps → Proposal → Revisão → Apply → Archive → Spec disponível
```

## Scope

### In Scope
- Novo comando `convert-next` para conversão incremental
- Gerador de proposals via LLM (`proposal_generator.py`)
- Loader de specs das dependências (`spec_context_loader.py`)
- Rastreador de status de conversão (`conversion_tracker.py`)
- Prompt específico para geração de proposals
- Proposals geradas em `output/openspec/` (separado do wxcode)

### Out of Scope
- Migração de conversões já feitas
- Interface web para revisão
- Conversão em batch sem revisão

## Success Criteria

1. `wxcode convert-next Linkpay_ADM` gera proposal para primeiro elemento
2. Proposal segue formato OpenSpec válido com `## ADDED Requirements`
3. `openspec validate {element}-spec` passa sem erros
4. Após archive, spec disponível em `output/openspec/specs/{element}-spec/`
5. Próximo elemento consegue acessar spec da dependência

## Risks

| Risco | Mitigação |
|-------|-----------|
| Proposals muito grandes | Limitar escopo por elemento, chunking se necessário |
| LLM gera spec inválida | Prompt ajustado para formato correto, validação automática |
| Muitos elementos para converter | Modo semi-automático permite pausar |
