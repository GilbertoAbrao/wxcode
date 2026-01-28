# Proposal: add-llm-procedure-converter

## Summary

Adicionar conversão LLM para procedures globais (.wdg), gerando services Python com a mesma qualidade que o PageConverter gera para páginas.

## Problem

Atualmente:
- `wxcode convert` usa LLM (PageConverter) para páginas → código inteligente
- `wxcode export` usa ServiceGenerator determinístico → código incompleto com `NotImplementedError`

O ServiceGenerator determinístico não consegue converter:
- Queries SQL complexas
- Lógica de negócio condicional
- Chamadas a APIs externas
- Tratamento de erros contextual

## Solution

Criar `ProcedureConverter` análogo ao `PageConverter`:

```
ProcedureConverter
├── ProcedureContextBuilder  → Monta contexto de procedures
├── LLMProvider              → Reutiliza provider existente
├── ServiceResponseParser    → Parseia resposta de service
└── ServiceOutputWriter      → Escreve arquivos de service
```

## Scope

### In Scope
- Converter procedure groups (.wdg) via LLM
- Gerar services Python async com type hints
- Converter queries H* para MongoDB
- Tratar dependências entre procedures
- CLI: `wxcode convert --layer service`

### Out of Scope
- Converter procedures browser (.wwn)
- Gerar testes automaticamente
- Conversão de procedures de relatório

## Success Criteria

1. `Global_FazLoginUsuarioInterno` gera código Python funcional (não stubs)
2. Custo por procedure < $0.05 (média)
3. 90%+ das procedures convertem sem intervenção manual

## Risks

| Risco | Mitigação |
|-------|-----------|
| Procedures grandes excedem limite de tokens | Chunking por procedure individual |
| Dependências circulares entre grupos | Resolver em ordem topológica |
| Custo alto para muitos grupos | Filtro por grupo específico |
