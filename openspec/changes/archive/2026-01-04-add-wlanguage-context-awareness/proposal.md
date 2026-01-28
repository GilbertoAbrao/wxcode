# Proposal: add-wlanguage-context-awareness

## Summary

Adicionar suporte a três aspectos críticos do WLanguage que são fundamentais para a conversão correta de projetos WinDev/WebDev:

1. **DataBinding**: Controles de UI vinculados a campos de tabelas do banco
2. **Buffer Global HyperFile**: Contexto de registro atual por tabela
3. **Funções H***: Categorização e conversão das funções HyperFile

## Motivation

Atualmente, o wxcode extrai controles de UI mas **não captura** a informação de binding entre controles e campos de tabelas. Isso é crítico porque:

- Em WinDev, `FileToScreen()` e `ScreenToFile()` sincronizam automaticamente dados
- Controles com binding precisam de lógica especial na conversão para FastAPI + Jinja2
- Sem essa informação, formulários convertidos perdem a conexão com os dados

Além disso, o paradigma de **buffer global por tabela** do WLanguage é incompatível com Python/web stateless, exigindo conversão consciente para evitar bugs sutis.

## Scope

### In Scope

- Adicionar model `DataBindingInfo` em `control.py`
- Extrair informação de binding do PDF (campo "Linked item")
- Categorizar funções H* por comportamento de buffer
- Criar documentação de padrões de conversão HyperFile → MongoDB/SQLAlchemy
- Atualizar `dependency_extractor.py` para rastrear uso de tabelas via binding

### Out of Scope

- Implementação do transpiler determinístico (proposta separada)
- Conversão automática de código (fase 4)
- Suporte a WinDev Mobile

## Capabilities

### CAP-1: Data Binding Extraction

Extrair e armazenar informação de binding entre controles UI e campos de tabelas.

**Spec**: `specs/data-binding/spec.md`

### CAP-2: HyperFile Buffer Context

Documentar e rastrear o modelo de buffer global do HyperFile para conversão consciente.

**Spec**: `specs/hyperfile-buffer/spec.md`

### CAP-3: HyperFile Functions Categorization

Categorizar funções H* por comportamento de buffer e criar mapeamento para conversão.

**Spec**: `specs/hyperfile-functions/spec.md`

## Dependencies

- **Requer**: `page-code-parsing` spec (já existe)
- **Requer**: `schema-parsing` spec (já existe) - para mapear tabelas referenciadas

## Risks

| Risk | Mitigation |
|------|------------|
| Binding pode estar em `internal_properties` (base64) | Usar PDF como fonte primária, internal_properties como fallback |
| Múltiplos formatos de binding (simples, complexo, variável) | Modelar todos os tipos no DataBindingInfo |
| Padrões HyperFile complexos (HAlias, etc.) | Marcar para revisão LLM quando não determinístico |

## Success Criteria

- [ ] Model `DataBindingInfo` adicionado e testado
- [ ] Parser PDF extrai "Linked item" para controles
- [ ] 80%+ dos controles com binding no projeto de referência são identificados
- [ ] Documentação de funções H* categorizada e revisada
- [ ] Testes cobrindo cenários principais de binding
