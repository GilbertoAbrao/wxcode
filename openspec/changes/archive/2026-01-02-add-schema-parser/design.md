# Design: add-schema-parser

## Architecture Overview

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   BD.xdd        │────▶│  XddParser   │────▶│  MongoDB    │
│   (XML)         │     │              │     │  (schemas)  │
└─────────────────┘     └──────────────┘     └─────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  Models:     │
                        │  - Schema    │
                        │  - Table     │
                        │  - Column    │
                        │  - Index     │
                        │  - Connection│
                        └──────────────┘
```

## Data Models

### DatabaseSchema (Beanie Document)

```python
class DatabaseSchema(Document):
    """Schema completo de um projeto WinDev."""
    project_id: PydanticObjectId
    source_file: str                    # "BD.ana/BD.xdd"
    version: int                        # GenNum do XML

    connections: list[SchemaConnection]
    tables: list[SchemaTable]

    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "schemas"
```

### SchemaConnection (Embedded)

```python
class SchemaConnection(BaseModel):
    """Conexão de banco definida na Analysis."""
    name: str                           # "CNX_BASE_HOMOLOG"
    type_code: int                      # 1 = SQL Server
    source: str                         # "192.168.10.13"
    database: str                       # "Sipbackoffice"
    user: Optional[str]
```

### SchemaTable (Embedded)

```python
class SchemaTable(BaseModel):
    """Tabela (FICHIER) da Analysis."""
    name: str                           # "Cliente"
    physical_name: str                  # NomPhysique
    connection_name: str                # Referência à conexão
    supports_null: bool                 # FicNullSupporte

    columns: list[SchemaColumn]
    indexes: list[SchemaIndex]
```

### SchemaColumn (Embedded)

```python
class SchemaColumn(BaseModel):
    """Coluna (RUBRIQUE) da Analysis."""
    name: str                           # "IDcliente"
    hyperfile_type: int                 # TYPE (2, 24, 25, etc.)
    python_type: str                    # "int", "str", "datetime"
    size: int                           # TAILLE
    nullable: bool                      # Null from INDICERUBRIQUE
    default_value: Optional[str]        # Valeur from INDICERUBRIQUE

    is_primary_key: bool                # TYPE_CLE == 1
    is_indexed: bool                    # TYPE_CLE > 0
    is_auto_increment: bool             # TYPE == 24
```

### SchemaIndex (Embedded)

```python
class SchemaIndex(BaseModel):
    """Índice inferido das colunas."""
    name: str                           # Gerado: "idx_{table}_{column}"
    columns: list[str]
    is_unique: bool                     # TYPE_CLE == 3
    is_primary: bool                    # TYPE_CLE == 1
```

## XddParser Implementation

### Class Structure

```python
class XddParser:
    """Parser para arquivos .xdd (Analysis WinDev)."""

    HYPERFILE_TYPE_MAP = {
        2: ("str", "Text"),
        3: ("int", "SmallInteger"),
        5: ("int", "Integer"),
        6: ("int", "BigInteger"),
        11: ("float", "Float"),
        14: ("date", "Date"),
        17: ("time", "Time"),
        24: ("int", "Integer"),  # Auto-increment
        25: ("int", "BigInteger"),  # FK
        29: ("str", "Text"),  # Memo
        34: ("datetime", "DateTime"),
        37: ("bool", "Boolean"),
        41: ("Decimal", "Numeric"),
    }

    def __init__(self, xdd_path: Path):
        self.xdd_path = xdd_path

    def parse(self) -> XddParseResult:
        """Parse o arquivo .xdd e retorna resultado."""

    def _parse_connections(self, root: ET.Element) -> list[SchemaConnection]:
        """Extrai conexões do XML."""

    def _parse_tables(self, root: ET.Element) -> list[SchemaTable]:
        """Extrai tabelas (FICHIER) do XML."""

    def _parse_columns(self, fichier: ET.Element) -> list[SchemaColumn]:
        """Extrai colunas (RUBRIQUE) de uma tabela."""

    def _map_hyperfile_type(self, type_code: int) -> tuple[str, str]:
        """Mapeia TYPE do HyperFile para Python e SQLAlchemy."""
```

### Parse Result

```python
@dataclass
class XddParseResult:
    """Resultado do parsing de um arquivo .xdd."""
    connections: list[SchemaConnection]
    tables: list[SchemaTable]
    version: int
    total_columns: int
    warnings: list[str]  # Tipos desconhecidos, etc.
```

## CLI Command

```bash
# Parse schema do projeto
wxcode parse-schema ./project-refs/Linkpay_ADM

# Output esperado:
# Projeto: Linkpay_ADM
# Arquivo: BD.ana/BD.xdd
# Conexões: 2
# Tabelas: 50
# Colunas: 942
# Schema salvo no MongoDB!
```

## File Discovery

O parser deve:
1. Receber path do projeto
2. Encontrar diretório `.ana` (ex: `BD.ana/`)
3. Localizar arquivo `.xdd` dentro dele
4. Parsear e armazenar

```python
def find_analysis_file(project_dir: Path) -> Optional[Path]:
    """Encontra o arquivo .xdd da Analysis."""
    for ana_dir in project_dir.glob("*.ana"):
        for xdd_file in ana_dir.glob("*.xdd"):
            return xdd_file
    return None
```

## Idempotency

Operação idempotente:
- Deleta schema anterior do projeto antes de inserir novo
- Permite re-executar sem duplicar dados

## Error Handling

1. **Arquivo não encontrado**: Erro claro indicando ausência de .ana/.xdd
2. **XML malformado**: Capturar ParseError com linha/coluna
3. **Tipo desconhecido**: Warning + mapear para `Any`
4. **Encoding**: Tentar ISO-8859-1, fallback UTF-8

## Testing Strategy

1. **Unit tests**: Parser isolado com XML de exemplo
2. **Integration test**: Projeto Linkpay_ADM real
3. **Edge cases**: Tabela vazia, tipos desconhecidos, encoding
