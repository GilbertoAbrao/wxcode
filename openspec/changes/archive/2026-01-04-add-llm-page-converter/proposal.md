# Proposal: add-llm-page-converter

## Summary

Implementar um conversor de páginas baseado em LLM (Claude) para transformar páginas WinDev/WebDev em FastAPI + Jinja2. Este conversor substitui a abordagem anterior baseada em templates determinísticos por uma abordagem mais flexível e inteligente usando Large Language Models.

## Motivation

A abordagem anterior usando templates Jinja2 determinísticos tinha limitações:

1. **Rigidez**: Templates fixos não conseguiam lidar com variações nas estruturas das páginas
2. **Contexto limitado**: Não considerava o código WLanguage dos eventos
3. **Conversão genérica**: Gerava código genérico que não refletia a lógica real da página
4. **Manutenção difícil**: Cada novo padrão de página exigia novos templates

A abordagem LLM-based resolve esses problemas:

1. **Flexibilidade**: LLM adapta a conversão ao contexto específico de cada página
2. **Contexto rico**: Recebe controles, eventos, procedures locais e dependências
3. **Conversão semântica**: Entende a intenção do código e gera equivalente Python
4. **Zero templates**: Não precisa de templates pré-definidos para cada padrão

## Scope

### In Scope

- Novo módulo `src/wxcode/llm_converter/` com componentes:
  - `ContextBuilder`: Monta o prompt com dados do MongoDB
  - `LLMClient`: Interface com API Claude
  - `ResponseParser`: Valida e parseia resposta JSON do LLM
  - `OutputWriter`: Escreve arquivos no projeto target
  - `PageConverter`: Orquestra a conversão de uma página
- Novo comando CLI `wxcode convert-page`
- Integração com StarterKit existente
- Suporte a páginas de tamanho variado (estratégias para páginas grandes)

### Out of Scope

- Conversão de outros tipos de elementos (classes, procedures globais, queries)
- Remoção dos generators template-based existentes (podem coexistir)
- Interface web para acompanhamento
- Conversão em batch de múltiplas páginas (será implementado posteriormente)

## Design

Ver [design.md](./design.md) para arquitetura detalhada.

## Spec Deltas

| Spec | Type | Description |
|------|------|-------------|
| llm-page-converter | NEW | Define componentes e comportamentos do conversor LLM |

## Risks

1. **Custo de API**: Cada conversão consome tokens da API Claude
   - Mitigação: Cache de conversões, otimização de contexto
2. **Inconsistência**: LLM pode gerar código ligeiramente diferente para entradas similares
   - Mitigação: Validação estrutural do output, testes de regressão
3. **Limites de contexto**: Páginas muito grandes podem exceder context window
   - Mitigação: Estratégias de chunking e summarização hierárquica

## Success Criteria

- [ ] PAGE_Login convertida corretamente para FastAPI + Jinja2
- [ ] Template gerado renderiza igual ao original
- [ ] Rota FastAPI funciona com GET e POST (login)
- [ ] Código Python gerado é executável sem erros
- [ ] Tempo de conversão < 30 segundos por página simples
