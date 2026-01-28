# Design: Procedure Parser

## Context
Arquivos .wdg são grupos de procedures WinDev em formato YAML-like proprietário. Cada arquivo pode conter múltiplas procedures, estruturas e código de inicialização. O parser precisa extrair essas informações para posterior conversão para Python.

**Stakeholders**: Desenvolvedores usando wxcode para migração

**Constraints**:
- Formato .wdg não é YAML padrão (usa indentação e `|1+` para blocos de código)
- Procedures podem ter tipos de retorno complexos (JSON, variant, classes)
- Código pode conter caracteres especiais e acentos (UTF-8)

## Goals / Non-Goals

**Goals:**
- Extrair todas as procedures de arquivos .wdg
- Parsear assinaturas completas (nome, parâmetros, tipos)
- Preservar código original para conversão
- Identificar dependências entre procedures

**Non-Goals:**
- Converter código WLanguage para Python (fase 4.3)
- Validar sintaxe WLanguage
- Executar ou simular procedures

## Decisions

### Decision 1: Usar parser customizado ao invés de YAML parser
**Rationale**: O formato .wdg usa `|1+` para blocos de código multiline que não é YAML válido. Um parser customizado oferece mais controle.

**Alternatives considered**:
- PyYAML com custom constructors: Rejeitado por limitações com `|1+`
- Regex puro: Rejeitado por fragilidade

### Decision 2: Armazenar procedures como documentos separados
**Rationale**: Permite queries individuais por procedure, facilita análise de dependências e conversão incremental.

**Schema**:
```python
class Procedure(Document):
    element_id: Link[Element]      # Referência ao .wdg pai
    project_id: Link[Project]
    name: str                      # Nome da procedure
    procedure_id: Optional[str]    # ID interno WinDev
    type_code: int                 # Tipo (15 = procedure normal)

    # Assinatura
    parameters: list[ProcedureParameter]
    return_type: Optional[str]

    # Código
    code: str                      # Código WLanguage original
    code_lines: int

    # Dependências
    calls_procedures: list[str]    # Procedures chamadas
    uses_files: list[str]          # Arquivos HyperFile usados
    uses_apis: list[str]           # APIs externas

    # Metadados
    has_documentation: bool
    is_public: bool
```

### Decision 3: Extrair dependências via regex
**Rationale**: Análise estática simples é suficiente para identificar chamadas de procedures e operações HyperFile sem necessidade de AST completo.

**Patterns**:
```python
# Chamada de procedure
r'\b([A-Z][a-zA-Z0-9_]+)\s*\('

# Operações HyperFile
r'\b(HReadFirst|HReadNext|HAdd|HModify|HDelete|HExecuteQuery)\s*\('

# REST/HTTP
r'\b(RESTSend|HTTPRequest|HTTPSend)\s*\('
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Formato .wdg pode variar entre versões WinDev | Testar com múltiplos projetos, adicionar fallbacks |
| Regex pode ter falsos positivos em strings | Aceitar imperfeição, refinar após análise |
| Procedures muito grandes podem impactar performance | Streaming, não carregar código em memória desnecessariamente |

## Migration Plan
Não aplicável - nova funcionalidade.

## Open Questions
- [ ] Como tratar procedures com mesmo nome em arquivos diferentes?
- [ ] Devemos parsear procedures locais de páginas (.wwh) também?
