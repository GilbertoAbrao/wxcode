# Design: extract-database-connections

## Context

Aplicações WinDev/WebDev definem conexões de banco de dados no arquivo Analysis (.xdd). Cada conexão tem um atributo `Type` que indica o tipo de banco (SQL Server, MySQL, PostgreSQL, Oracle, HyperFile, etc.).

### Estrutura XML do .xdd

```xml
<CONNEXION Nom="CNX_BASE_HOMOLOG" Type="1">
  <SOURCE>192.168.10.13</SOURCE>
  <USER>infiniti_all</USER>
  <MDP/>
  <DB>Sipbackoffice_Virtualpay</DB>
  <INFOS_ETENDUES>;Initial Catalog=Sipbackoffice_Virtualpay</INFOS_ETENDUES>
</CONNEXION>
```

### Constantes WLanguage (hNativeAccess*)

De acordo com a documentação PCSoft e análise do código fonte:
- `hNativeAccessSQLServer` - SQL Server via Native Access
- `hNativeAccessMySQL` - MySQL via Native Access
- `hNativeAccessPostgreSQL` - PostgreSQL via Native Access
- `hNativeAccessOracle` - Oracle via Native Access
- `hOledbSQLServer` - SQL Server via OLE DB
- `hAccessHFClientServer` - HyperFile Client/Server

## Architecture

### 1. Connection Type Mapping

Criar mapeamento em `xdd_parser.py`:

```python
CONNECTION_TYPE_MAP: dict[int, tuple[str, str, str]] = {
    # Type: (database_type, driver_name, default_port)
    1: ("sqlserver", "SQL Server", "1433"),
    2: ("mysql", "MySQL", "3306"),
    3: ("postgresql", "PostgreSQL", "5432"),
    4: ("oracle", "Oracle", "1521"),
    5: ("hyperfile", "HyperFile Classic", ""),
    6: ("hyperfile_cs", "HyperFile C/S", "4900"),
    7: ("odbc", "ODBC", ""),
}
```

### 2. SchemaConnection Model Update

Adicionar campos ao `models/schema.py`:

```python
class SchemaConnection(BaseModel):
    name: str
    type_code: int
    database_type: str = ""  # NEW: "sqlserver", "mysql", "postgresql", etc.
    driver_name: str = ""    # NEW: Human-readable name
    source: str = ""
    port: str = ""           # NEW: Porta extraída ou default
    database: str = ""
    user: Optional[str] = None
    extended_info: str = ""  # NEW: INFOS_ETENDUES para parsing adicional
```

### 3. StarterKit Dynamic .env.example

Gerar `.env.example` baseado nas conexões:

```python
def _generate_env_example(self, connections: list[SchemaConnection]) -> None:
    """Generate .env.example from actual database connections."""
    content = "# Application\n"
    content += f"APP_NAME={self.config.project_name}\n"
    content += "DEBUG=false\n\n"

    for conn in connections:
        content += f"# Database: {conn.name}\n"
        content += self._generate_connection_env(conn)
        content += "\n"
```

Exemplo de saída:

```env
# Application
APP_NAME=Linkpay_ADM
DEBUG=false

# Database: CNX_BASE_HOMOLOG
CNX_BASE_HOMOLOG_HOST=192.168.10.13
CNX_BASE_HOMOLOG_PORT=1433
CNX_BASE_HOMOLOG_DATABASE=Sipbackoffice_Virtualpay
CNX_BASE_HOMOLOG_USER=infiniti_all
CNX_BASE_HOMOLOG_PASSWORD=
CNX_BASE_HOMOLOG_TYPE=sqlserver

# Database: BdInfiniti
BDINFINITI_HOST=192.168.10.13
BDINFINITI_PORT=1433
BDINFINITI_DATABASE=Sipbackoffice_VirtualPay
BDINFINITI_USER=infiniti_all
BDINFINITI_PASSWORD=
BDINFINITI_TYPE=sqlserver
```

### 4. database.py Multi-Connection Support

Gerar código que registra múltiplas conexões:

```python
# Generated database.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConnection:
    name: str
    engine: Any  # SQLAlchemy engine ou Motor client
    session_factory: Any

connections: dict[str, DatabaseConnection] = {}

async def init_db() -> None:
    """Initialize all database connections."""
    # CNX_BASE_HOMOLOG
    engine_cnx_base = create_async_engine(
        f"mssql+aioodbc://{settings.cnx_base_homolog_user}:..."
    )
    connections["CNX_BASE_HOMOLOG"] = DatabaseConnection(...)

    # BdInfiniti
    engine_bdinfiniti = create_async_engine(...)
    connections["BdInfiniti"] = DatabaseConnection(...)

def get_db(connection_name: str = "CNX_BASE_HOMOLOG"):
    """Get database session for specific connection."""
    return connections[connection_name].session_factory()
```

## Decision: Database Driver Strategy

### Option A: SQLAlchemy com drivers async
- **Pros:** Unificado, ORM maduro, suporte amplo
- **Cons:** Precisa de drivers específicos (aioodbc, asyncpg, aiomysql)

### Option B: Connection pools específicos por tipo
- **Pros:** Performance otimizada por banco
- **Cons:** Mais código, menos unificado

**Decisão:** Option A - SQLAlchemy como abstração, com geração de requirements.txt incluindo drivers necessários.

## Driver Requirements por Tipo

| Database Type | SQLAlchemy Driver | Python Package |
|--------------|-------------------|----------------|
| sqlserver | mssql+aioodbc | aioodbc |
| postgresql | postgresql+asyncpg | asyncpg |
| mysql | mysql+aiomysql | aiomysql |
| oracle | oracle+oracledb | python-oracledb |
| hyperfile | N/A | httpx (REST API) |

## Edge Cases

1. **Conexões sem tipo definido (Type=0):** Usar "unknown", não gerar config
2. **Múltiplas conexões mesmo tipo:** Gerar com prefixo único do nome da conexão
3. **HyperFile:** Não suportado via SQLAlchemy, gerar comentário indicando necessidade de REST API ou HyperFile SDK
4. **Senha em branco (MDP vazio):** Gerar variável vazia, usuário preenche manualmente

## Files to Modify

1. `src/wxcode/parser/xdd_parser.py` - Adicionar mapeamento de tipos
2. `src/wxcode/models/schema.py` - Atualizar SchemaConnection
3. `src/wxcode/generator/starter_kit.py` - Geração dinâmica de .env.example e database.py
4. `src/wxcode/generator/orchestrator.py` - Passar conexões para StarterKit
