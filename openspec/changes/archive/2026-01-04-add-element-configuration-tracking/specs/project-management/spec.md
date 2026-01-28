# project-management Specification Delta

## ADDED Requirements

### Requirement: Element Configuration Tracking

O sistema SHALL extrair e armazenar as configurações de build em que cada elemento está excluído durante a importação do projeto.

#### Scenario: Element excluded from one configuration

- **GIVEN** um arquivo .wwp com elemento que tem:
  ```yaml
  configurations :
    -
      configuration_id : 13051986534836779703
      excluded : true
    -
      configuration_id : 917926033879572243
  ```
- **WHEN** executamos `wxcode import projeto.wwp`
- **THEN** o Element deve ter `excluded_from: ["13051986534836779703"]`
- **AND** a configuração sem `excluded` (ou `excluded: false`) NÃO deve aparecer na lista

#### Scenario: Element included in all configurations

- **GIVEN** um arquivo .wwp com elemento que tem:
  ```yaml
  configurations :
    -
      configuration_id : 13051986534836779703
    -
      configuration_id : 917926033879572243
  ```
- **WHEN** executamos `wxcode import projeto.wwp`
- **THEN** o Element deve ter `excluded_from: []`

#### Scenario: Element excluded from multiple configurations

- **GIVEN** um arquivo .wwp com elemento que tem:
  ```yaml
  configurations :
    -
      configuration_id : 111111111111111111
      excluded : true
    -
      configuration_id : 222222222222222222
      excluded : true
    -
      configuration_id : 333333333333333333
  ```
- **WHEN** executamos `wxcode import projeto.wwp`
- **THEN** o Element deve ter `excluded_from: ["111111111111111111", "222222222222222222"]`

#### Scenario: Element without configurations section

- **GIVEN** um arquivo .wwp com elemento que NÃO tem seção `configurations :`
- **WHEN** executamos `wxcode import projeto.wwp`
- **THEN** o Element deve ter `excluded_from: []`

---
