# Proposal: add-element-configuration-tracking

## Problem Statement

Atualmente o `project_mapper.py` extrai os elementos do arquivo `.wwp`, mas **não captura** a seção `configurations` aninhada dentro de cada elemento. Essa seção indica em quais configurações de build (Producao, Staging, Debug, etc.) cada elemento está incluído ou excluído.

Exemplo da estrutura no arquivo `.wwp`:
```yaml
- name : PAGE_Login
  identifier : 0x4f8875dc006ef2e4
  physical_name : .\PAGE_Login.wwh
  type : 65538
  configurations :          # <-- NÃO ESTAMOS CAPTURANDO
    -
      configuration_id : 13051986534836779703
      excluded : true       # <-- Excluído da config STAGING
    -
      configuration_id : 917926033879572243
                           # <-- Incluído na config Producao (sem excluded = incluído)
```

O model `Element` já possui o campo `excluded_from: list[str]` preparado, mas ele nunca é populado.

## Proposed Solution

Modificar o `project_mapper.py` para:

1. Detectar a seção `configurations :` dentro de cada elemento
2. Parsear os items da lista, extraindo `configuration_id` e `excluded`
3. Popular o campo `excluded_from` com os IDs das configurações onde `excluded : true`

### Escopo

- **IN SCOPE:**
  - Modificar `project_mapper.py` para extrair configurations por elemento
  - Popular campo `excluded_from` no Element
  - Adicionar testes para o novo comportamento

- **OUT OF SCOPE:**
  - Usar essa informação na conversão (será outro change)
  - Mapear configuration_id para nomes de configuração (já temos via Project.configurations)

## Impact Analysis

### Files to Modify
| File | Change |
|------|--------|
| `src/wxcode/parser/project_mapper.py` | Adicionar parsing de configurations por elemento |

### Backward Compatibility
- Elementos existentes no MongoDB continuarão com `excluded_from: []`
- Reimportação com `--force` irá popular o campo corretamente

## Acceptance Criteria

1. Após `wxcode import`, elementos devem ter `excluded_from` populado
2. Elementos incluídos em todas as configs devem ter `excluded_from: []`
3. Elementos excluídos de alguma config devem ter os IDs correspondentes em `excluded_from`
