# control-enrichment Specification Delta

## Purpose
Define como controles de UI são enriquecidos com propriedades visuais do PDF de documentação.

## MODIFIED Requirements

### Requirement: PDF Splitting - Element Detection
O `PDFDocSplitter` MUST detectar apenas elementos reais do projeto WinDev.

#### Scenario: Detectar páginas reais
- Given PDF com título "PAGE_LOGIN"
- When split-pdf executa
- Then PDF individual criado para PAGE_LOGIN

#### Scenario: Ignorar POPUPs
- Given PDF com título "POPUP_ITEM"
- When split-pdf executa
- Then NENHUM PDF individual criado para POPUP_ITEM

#### Scenario: Ignorar containers
- Given PDF com títulos "ZONE_NoName1", "CELL_Header", "MENU_Principal"
- When split-pdf executa
- Then NENHUM PDF individual criado para esses containers

#### Scenario: Detectar reports
- Given PDF com título "RPT_VENDAS"
- When split-pdf executa
- Then PDF individual criado para RPT_VENDAS

---

### Requirement: Control Matching - Container Controls
O `ElementEnricher` MUST fazer matching de controles dentro de containers usando o PDF do elemento pai.

#### Scenario: Controle dentro de POPUP
- Given controle "POPUP_ITEM.EDT_NOME" no .wwh
- And PDF do elemento pai contém "POPUP_ITEM.EDT_NOME" com Height=30
- When enrich executa
- Then controle tem properties.height = 30
- And is_orphan = false

#### Scenario: Controle dentro de ZONE
- Given controle "ZONE_NoName2.TABLE_LISTA.COL_ID" no .wwh
- And PDF do elemento pai contém esse path
- When enrich executa
- Then controle tem propriedades do PDF
- And is_orphan = false

#### Scenario: Controle aninhado múltiplos níveis
- Given controle "ZONE_NoName2.CELL_Header.BTN_SALVAR" no .wwh
- And PDF contém path completo
- When enrich executa
- Then matching por leaf name (BTN_SALVAR) funciona

---

### Requirement: Single Matching Context
O `ElementEnricher` MUST usar um único contexto de matching por elemento.

#### Scenario: Sem contextos separados para POPUPs
- Given página com múltiplos POPUPs
- When enrich executa
- Then apenas UM MatchingContext criado (do PDF da página)
- And todos os controles (incluindo de POPUPs) buscam nesse contexto

#### Scenario: Path completo no PDF
- Given PDF da página FORM_GRUPO_COBRANCA
- When parser extrai controles
- Then controles listados com path completo: "POPUP_ITEM.EDT_NOME"

---

## REMOVED Requirements

### Requirement: POPUP PDF Loading (REMOVED)
~~O `ElementEnricher` MUST carregar PDFs separados para POPUPs.~~

**Motivo da remoção:** POPUPs são controles, não elementos. Seus controles estão documentados no PDF da página pai.

### Requirement: POPUP Context Building (REMOVED)
~~O `ElementEnricher` MUST construir contextos de matching separados para POPUPs.~~

**Motivo da remoção:** Um único contexto por elemento é suficiente, pois o PDF contém todos os controles com paths completos.

---

## ADDED Requirements

### Requirement: PDF Control Name Recognition
O `PDFElementParser` MUST reconhecer nomes de controles com paths de containers.

#### Scenario: Path com POPUP
- Given linha "POPUP_ITEM.EDT_NOME" no PDF
- When parser verifica _is_control_name()
- Then retorna True

#### Scenario: Path com múltiplos containers
- Given linha "ZONE_NoName2.CELL_Header.TABLE_Lista.COL_ID"
- When parser verifica _is_control_name()
- Then retorna True (leaf COL_ID tem prefixo conhecido)

#### Scenario: Alias ignorado
- Given linha "A35" (alias interno)
- When parser verifica _is_control_name()
- Then retorna False (não tem prefixo conhecido)
