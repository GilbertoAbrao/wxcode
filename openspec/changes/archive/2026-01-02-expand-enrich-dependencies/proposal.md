# Proposal: expand-enrich-dependencies

## Summary
Expandir o comando `enrich` para extrair procedures locais de páginas/windows e analisar dependências de todo o código (procedures locais + eventos de controles).

## Motivation
O grafo de dependências (Fase 3.1) precisa de dados completos para calcular a ordem topológica de conversão. Atualmente:

| Fonte | Procedures | Dependências |
|-------|------------|--------------|
| `.wdg` (globais) | ✅ 371 parseadas | ✅ Extraídas |
| `.wdc` (classes) | ✅ 14 parseadas | ✅ Extraídas |
| `.wwh` (páginas) | ❌ **~207 não extraídas** | ❌ Não extraídas |
| Eventos de controles | - | ❌ **253 com código não analisado** |

Sem essas dependências, o grafo estará incompleto e a ordem de conversão será incorreta.

## Current State

### O que o `enrich` faz hoje:
1. ✅ Parseia arquivo `.wwh/.wdw` via `WWHParser`
2. ✅ Extrai controles com eventos (código incluído)
3. ✅ Parseia PDF de documentação (propriedades visuais)
4. ✅ Salva controles na collection `controls`
5. ✅ Atualiza `Element.controls_count`

### O que está faltando:
1. ❌ Extrair procedures locais → collection `procedures`
2. ❌ Analisar código das procedures locais → dependências
3. ❌ Analisar código dos eventos dos controles → dependências
4. ❌ Agregar dependências no `Element.dependencies`

### Dados no MongoDB:
- **253 controles** com código nos eventos (não analisado)
- **~207 procedures locais** nas páginas (não extraídas)
- `Element.dependencies` está **vazio** para páginas

## Proposed Solution

### 1. Extrair Procedures Locais
O `WWHParser` já parseia o arquivo. Adicionar extração de procedures locais:

```python
# Em wwh_parser.py ou novo módulo
class ParsedLocalProcedure:
    name: str
    parameters: list[ParsedParameter]
    return_type: Optional[str]
    code: str
    code_lines: int

class ParsedPage:
    # ... campos existentes ...
    local_procedures: list[ParsedLocalProcedure]  # NOVO
```

### 2. Analisar Dependências
Reutilizar lógica do `wdg_parser._extract_dependencies()`:

```python
# Regex existentes no wdg_parser:
PROCEDURE_CALL_RE  # Detecta chamadas de procedures
HYPERFILE_RE       # Detecta operações HyperFile
CLASS_INSTANTIATION_RE  # Detecta uso de classes (NOVO)
```

### 3. Agregar no Element
```python
# Após processar página:
element.dependencies = ElementDependencies(
    uses=all_procedures_called,      # Procedures chamadas
    data_files=all_tables_used,      # Tabelas HyperFile
    used_by=[],                      # Preenchido pelo grafo
    external_apis=apis_detected,
)
```

### 4. Salvar Procedures Locais
```python
# Salvar na collection procedures (como wdg_parser faz)
for local_proc in parsed_page.local_procedures:
    procedure = Procedure(
        project_id=project.id,
        element_id=element.id,
        name=local_proc.name,
        is_local=True,  # NOVO campo para distinguir
        # ... outros campos
    )
    await procedure.insert()
```

## Scope

### In scope:
- Extrair procedures locais de páginas/windows
- Analisar dependências das procedures locais
- Analisar dependências dos eventos dos controles
- Agregar dependências no `Element.dependencies`
- Salvar procedures locais na collection `procedures`
- Adicionar campo `is_local` ao model `Procedure`

### Out of scope:
- Construção do grafo (próxima proposta)
- Reports (`.wde`) - podem não ter procedures locais
- Browser procedures (`.wwn`) - são JavaScript, não WLanguage

## CLI Changes

O comando `enrich` existente será expandido. Novo output:

```
Enriching: PAGE_PRINCIPAL
  ✓ Controls: 18 parsed
  ✓ Local procedures: 3 extracted
  ✓ Dependencies: 12 procedures, 5 tables, 2 classes

Summary:
  Elements processed: 100
  Controls created: 1,965
  Local procedures: 207
  Dependencies extracted: 1,523
```

## Dependencies
- Specs existentes: `procedure-parsing` (reutilizar modelos e regex)
- `WWHParser` já parseia o código

## Risks
1. **Procedures duplicadas**: Mesmo nome em páginas diferentes
   - Mitigação: Incluir `element_id` como parte da identificação

2. **Performance**: Analisar código de 253 controles + 207 procedures
   - Mitigação: Já é O(n) no enrich, adiciona overhead mínimo

3. **Código incompleto**: Alguns eventos podem ter código parcial
   - Mitigação: Tratar erros graciosamente, logar warnings
