# control-matching Specification

## Purpose
Define o algoritmo de matching entre controles extraídos do PDF de documentação e do arquivo fonte (.wwh/.wdw), minimizando controles órfãos.

## ADDED Requirements

### Requirement: Multi-Phase Control Matching
O sistema MUST usar algoritmo de matching em 3 fases para associar controles do PDF com controles do .wwh.

#### Scenario: Match exato por full_path
- Given controle do .wwh com full_path "ZONE_NoName1.EDT_NOME"
- And PDF contém controle com mesmo full_path "ZONE_NoName1.EDT_NOME"
- When matching é executado
- Then controle é matched (não órfão)
- And propriedades do PDF são associadas

#### Scenario: Match exato por name
- Given controle do .wwh com name "BTN_SALVAR"
- And PDF contém controle com mesmo name "BTN_SALVAR"
- And full_path não coincide
- When matching é executado
- Then controle é matched
- And propriedades do PDF são associadas

#### Scenario: Match por leaf name
- Given controle do .wwh com full_path "POPUP_ITEM.EDT_NOME"
- And PDF contém controle "ZONE_NoName2.EDT_NOME"
- And "EDT_NOME" é único no PDF (apenas 1 ocorrência)
- When matching é executado
- Then controle é matched por leaf name
- And container mapping é registrado: POPUP_ITEM → ZONE_NoName2

#### Scenario: Match ambíguo permanece órfão
- Given controle do .wwh com name "STC_NoName1"
- And PDF contém múltiplos controles com leaf name "STC_NoName1"
- When matching é executado
- Then controle permanece órfão
- And warning é logado indicando ambiguidade

---

### Requirement: Container Mapping Propagation
O sistema MUST propagar mapeamentos de containers descobertos para resolver mais órfãos.

#### Scenario: Propagação para filhos do mesmo container
- Given container mapping descoberto: POPUP_ITEM → ZONE_NoName2
- And controle órfão com full_path "POPUP_ITEM.BTN_X"
- And PDF contém "ZONE_NoName2.BTN_X"
- When matching é reprocessado
- Then controle é matched usando mapeamento propagado
- And propriedades do PDF são associadas

#### Scenario: Múltiplos níveis de aninhamento
- Given container mapping: POPUP_ITEM → ZONE_NoName2
- And controle órfão "POPUP_ITEM.CELL_1.EDT_CAMPO"
- And PDF contém "ZONE_NoName2.CELL_1.EDT_CAMPO"
- When matching é executado
- Then controle é matched substituindo apenas o container raiz

---

### Requirement: Matching Statistics
O sistema MUST reportar estatísticas detalhadas do processo de matching.

#### Scenario: Estatísticas no resultado do enriquecimento
- Given enriquecimento executado
- When resultado é retornado
- Then contém contagem de: exact_matches, leaf_matches, propagated_matches, ambiguous, orphans

#### Scenario: Log de resumo
- Given enriquecimento concluído
- When logs são emitidos
- Then contém linha: "Matching: X exact, Y by-leaf, Z propagated, W ambiguous, N orphans"

---

### Requirement: Backward Compatibility
O sistema MUST manter comportamento correto quando PDF não está disponível.

#### Scenario: Sem PDF disponível
- Given elemento sem PDF correspondente
- When enriquecimento é executado
- Then todos os controles são marcados como órfãos
- And nenhum erro é lançado
- And warning é logado

#### Scenario: PDF vazio
- Given PDF parseado sem controles
- When enriquecimento é executado
- Then todos os controles são marcados como órfãos
- And processamento continua normalmente
