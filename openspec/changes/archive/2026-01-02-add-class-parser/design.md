# Design: add-class-parser

## Análise do Formato .wdc

Arquivos .wdc usam formato YAML similar ao .wdg:

```yaml
info:
  name: classUsuario
  type: 4                    # Tipo = Classe
class:
  identifier: 0x125f4ca...
  code_elements:
    type_code: 10
    p_codes:
      - code: |1+
          classUsuario is a Class
            inherits _classBasic

            PROTECTED
            _campo is string

            PUBLIC
            Nome is string
          end
        type: 131072
  procedures:
    - name: Constructor
      type_code: 27          # Constructor
      code: |1+ ...
    - name: Destructor
      type_code: 28          # Destructor
    - name: Salvar
      type_code: 12          # Método normal
      code: |1+ ...
```

## Type Codes Relevantes

| type_code | Significado |
|-----------|-------------|
| 10 | Definição de classe (code_elements) |
| 12 | Método normal |
| 27 | Constructor |
| 28 | Destructor |

## Estrutura de Dados

### ClassMember
```python
class ClassMember(BaseModel):
    name: str
    type: str                    # string, int, datetime, etc.
    visibility: str              # public, private, protected
    default_value: Optional[str]
    serialize: bool = True       # Se tem Serialize = false
```

### ClassMethod
Reutiliza estrutura similar a `Procedure`:
```python
class ClassMethod(BaseModel):
    name: str
    method_type: str             # constructor, destructor, method
    visibility: str
    parameters: list[ProcedureParameter]
    return_type: Optional[str]
    code: str
    code_lines: int
    is_static: bool = False
```

### ClassConstant
```python
class ClassConstant(BaseModel):
    name: str
    value: str
    type: Optional[str]
```

### ClassDefinition (Document)
```python
class ClassDefinition(Document):
    project_id: PydanticObjectId
    element_id: PydanticObjectId

    name: str
    inherits_from: Optional[str]
    is_abstract: bool

    members: list[ClassMember]
    methods: list[ClassMethod]
    constants: list[ClassConstant]

    dependencies: ClassDependencies
```

## Fluxo de Parsing

```
1. Lê arquivo .wdc
2. Extrai seção `info.name`
3. Extrai `class.code_elements.p_codes[0].code` → definição da classe
4. Parse definição:
   - Nome e modificadores (abstract)
   - Herança (inherits)
   - Blocos de visibilidade (PUBLIC, PRIVATE, PROTECTED)
   - Membros com tipos e defaults
5. Extrai `class.procedures` → métodos
6. Identifica dependências no código
7. Salva ClassDefinition no MongoDB
```

## Regex Patterns

```python
# Definição de classe
CLASS_DEF_RE = r'^(\w+)\s+is\s+(?:a\s+)?Class(?:\s*,\s*abstract)?'

# Herança
INHERITS_RE = r'inherits\s+(?:from\s+)?(\w+)'

# Blocos de visibilidade
VISIBILITY_BLOCK_RE = r'^(PUBLIC|PRIVATE|PROTECTED)\s*$'

# Membro
MEMBER_RE = r'^\s*(\w+)\s+is\s+(.+?)(?:\s*=\s*(.+?))?(?:\s*,\s*(.+))?$'
```

## Decisões

1. **Reutilizar ProcedureParameter**: Métodos de classe usam mesma estrutura de parâmetros que procedures
2. **ClassMethod separado de Procedure**: Métodos têm semântica diferente (visibility, static, method_type)
3. **Armazenar em collection separada**: `class_definitions` em vez de reaproveitar `procedures`
4. **Índices por herança**: Permitir queries como "todas classes que herdam de _classBasic"
