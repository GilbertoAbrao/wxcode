# page-code-parsing Specification

## Purpose
Extrair procedures locais e dependências de páginas/windows durante o enriquecimento.

## ADDED Requirements

### Requirement: Extract Local Procedures
O `WWHParser` MUST extrair procedures locais definidas em páginas/windows.

#### Scenario: Procedure local simples
- Given página com `procedure Local_Display_Time()`
- When parser executa
- Then `local_procedures` contém procedure com name="Local_Display_Time"

#### Scenario: Procedure com parâmetros
- Given página com `procedure Local_Listar(bNovoPeriodo is boolean)`
- When parser executa
- Then procedure tem parameters=[{name: "bNovoPeriodo", type: "boolean"}]

#### Scenario: Procedure com retorno
- Given página com `procedure Local_Calcular(): int`
- When parser executa
- Then procedure tem return_type="int"

#### Scenario: Múltiplas procedures
- Given página com 3 procedures locais
- When parser executa
- Then `local_procedures` tem length=3

---

### Requirement: Extract Dependencies from Code
O sistema MUST extrair dependências de qualquer bloco de código WLanguage.

#### Scenario: Detectar chamada de procedure
- Given código `resultado = BuscaCEP(sCEP)`
- When DependencyExtractor.extract() executa
- Then calls_procedures contém "BuscaCEP"

#### Scenario: Detectar operação HyperFile
- Given código `HReadSeekFirst(Cliente, CPF, sCPF)`
- When DependencyExtractor.extract() executa
- Then uses_files contém "Cliente"

#### Scenario: Detectar uso de classe
- Given código `objUsuario is classUsuario`
- When DependencyExtractor.extract() executa
- Then uses_classes contém "classUsuario"

#### Scenario: Ignorar funções built-in
- Given código `Length(sTexto) + Val(sNumero)`
- When DependencyExtractor.extract() executa
- Then calls_procedures NÃO contém "Length" nem "Val"

#### Scenario: Detectar chamada de API REST
- Given código `RESTSend(cRequest)`
- When DependencyExtractor.extract() executa
- Then uses_apis contém "REST"

---

### Requirement: Save Local Procedures to MongoDB
O `ElementEnricher` MUST salvar procedures locais na collection `procedures`.

#### Scenario: Procedure local salva
- Given página com procedure local "Local_Calcular"
- When enrich executa
- Then Procedure document criado com is_local=True

#### Scenario: Scope definido
- Given página .wwh com procedure local
- When enrich executa
- Then Procedure.scope = "page"

#### Scenario: Window scope
- Given window .wdw com procedure local
- When enrich executa
- Then Procedure.scope = "window"

#### Scenario: Element reference
- Given procedure local da PAGE_LOGIN
- When salva no MongoDB
- Then Procedure.element_id = ObjectId da PAGE_LOGIN

---

### Requirement: Aggregate Dependencies in Element
O `ElementEnricher` MUST agregar dependências de todas as fontes no Element.

#### Scenario: Dependências de eventos de página
- Given página com OnLoad que chama "InitPage()"
- When enrich executa
- Then Element.dependencies.uses contém "InitPage"

#### Scenario: Dependências de eventos de controles
- Given controle BTN_Salvar com OnClick que chama "Salvar()"
- When enrich executa
- Then Element.dependencies.uses contém "Salvar"

#### Scenario: Dependências de procedures locais
- Given procedure local que usa `HAdd(Cliente)`
- When enrich executa
- Then Element.dependencies.data_files contém "Cliente"

#### Scenario: Merge de múltiplas fontes
- Given página com:
  - Evento OnLoad chamando "ProcA"
  - Controle chamando "ProcB"
  - Procedure local chamando "ProcC"
- When enrich executa
- Then Element.dependencies.uses contém ["ProcA", "ProcB", "ProcC"]

#### Scenario: Sem duplicatas
- Given múltiplos eventos chamando "MesmaProc"
- When enrich executa
- Then Element.dependencies.uses contém "MesmaProc" apenas uma vez

---

### Requirement: Updated CLI Output
O comando `enrich` MUST exibir estatísticas das novas extrações.

#### Scenario: Mostrar procedures locais
- Given enrich processou 10 páginas com 25 procedures locais
- When exibe resultado
- Then summary mostra "Local procedures: 25"

#### Scenario: Mostrar dependências
- Given enrich extraiu 150 dependências
- When exibe resultado
- Then summary mostra "Dependencies extracted: 150"

---

### Requirement: Procedure Model Extension
O model `Procedure` MUST ter campos para distinguir procedures locais.

#### Scenario: Campo is_local
- Given Procedure criada para procedure de página
- When is_local=True
- Then pode ser filtrada com Procedure.find({"is_local": True})

#### Scenario: Campo scope
- Given Procedure de página
- When scope="page"
- Then indica que pertence a uma página (vs window ou report)

#### Scenario: Backward compatibility
- Given procedures globais existentes (de .wdg)
- When migration roda
- Then is_local=False por padrão
- And dados existentes não afetados
