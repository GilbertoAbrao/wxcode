# Proposal: Improve Control Matching

## Change ID
`improve-control-matching`

## Summary
Melhorar o algoritmo de matching entre controles do PDF e do .wwh para reduzir controles órfãos. Atualmente ~15% dos controles são órfãos porque containers têm nomes diferentes entre as fontes (ex: `ZONE_NoName2` no PDF vs `POPUP_ITEM` no .wwh).

## Motivation

### Problema
O enricher marca controles como "órfãos" quando não encontra match entre PDF e .wwh. Atualmente o matching é feito apenas por:
1. `full_path` exato
2. `name` exato

Isso falha quando:
- O PDF usa nomes genéricos para containers (`ZONE_NoName1`, `ZONE_NoName2`)
- O .wwh usa nomes semânticos para os mesmos containers (`POPUP_ITEM`, `POPUP_CLIENTE`)
- Resultado: todos os filhos desse container viram órfãos

### Evidência
No projeto Linkpay_ADM:
- **2188 controles** totais
- **329 controles órfãos** (~15%)
- Maioria são filhos de POPUPs

Exemplo concreto:
```
PDF:  ZONE_NoName2.EDT_NOME
WWH:  POPUP_ITEM.EDT_NOME
```
Mesmo controle `EDT_NOME`, mas pais diferentes = órfão.

### Impacto
Controles órfãos perdem:
- Propriedades visuais (altura, largura, posição)
- Estilos e tooltips
- Informações de layout

Isso afeta a qualidade da conversão para templates Jinja2.

## Scope

### In Scope
1. Adicionar estratégia de **matching por nome de folha** (leaf name)
2. Para controles filhos, tentar match ignorando o container pai
3. Construir mapa de correspondência container→container baseado em filhos matched

### Out of Scope
- Match por posição/dimensões (requer coordenadas exatas)
- Match por tipo de controle (type_code)
- Refatoração completa do enricher
- Alterações no PDF parser

## Success Criteria
1. Reduzir controles órfãos de ~329 para <50 no projeto Linkpay_ADM
2. Manter 100% de cobertura dos controles que já fazem match
3. Não degradar performance significativamente (<10% overhead)

## Dependencies
- Spec existente: `page-code-parsing` (padrão de enriquecimento)

## Risks and Mitigations

| Risco | Mitigação |
|-------|-----------|
| Match incorreto de controles com mesmo nome | Priorizar full_path exato, usar leaf como fallback |
| Múltiplos controles com mesmo leaf name | Usar primeiro match ou ignorar ambíguos |
| Containers incorretamente mapeados | Log de warnings para revisão manual |
