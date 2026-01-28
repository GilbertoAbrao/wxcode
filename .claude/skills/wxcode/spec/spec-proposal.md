---
name: wx:spec-proposal
description: Gera proposta de especificação OpenSpec para conversão de elemento.
allowed-tools: Bash
---

# wx:spec-proposal - Gerar Proposta de Spec

Analisa um elemento e gera uma proposta OpenSpec para sua conversão.

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `project_name` | string | Sim | Nome do projeto |
| `element_name` | string | Sim | Nome do elemento |
| `--output` | path | Não | Diretório de saída |

## Uso

```bash
wxcode spec-proposal <project> <element> [--output DIR]
```

## Exemplos

```bash
# Gerar proposta para página
wxcode spec-proposal Linkpay_ADM PAGE_Login

# Especificar output
wxcode spec-proposal Linkpay_ADM PAGE_CadCliente --output ./specs
```

## O que é gerado

Estrutura OpenSpec completa:

```
openspec/changes/convert-PAGE_Login/
├── proposal.md       # Resumo e motivação
├── design.md         # Decisões arquiteturais
├── tasks.md          # Tasks de implementação
└── specs/
    └── page-login/
        └── spec.md   # Requirements e scenarios
```

## Saída esperada

```
Generating spec proposal: PAGE_Login

Analyzing element...
  Type: page
  Controls: 42
  Events: 8
  Dependencies: 5

Generating proposal...
  ✓ proposal.md
  ✓ design.md
  ✓ tasks.md
  ✓ specs/page-login/spec.md

Proposal created at:
  openspec/changes/convert-PAGE_Login/

Next steps:
  1. Review: openspec show convert-PAGE_Login
  2. Validate: openspec validate convert-PAGE_Login
  3. Apply: /openspec:apply convert-PAGE_Login
```

## Conteúdo da Proposta

A proposta inclui:
- **Requirements**: O que deve ser implementado
- **Scenarios**: Casos de teste
- **Tasks**: Passos de implementação
- **Design**: Decisões técnicas

## Integração OpenSpec

Após gerar a proposta:
```bash
# Validar
openspec validate convert-PAGE_Login

# Aplicar (via skill)
/openspec:apply convert-PAGE_Login
```
