# schema-parsing Spec Delta

## MODIFIED Requirements

### Requirement: XDD-CONN-001 - Extract Connections
O parser MUST extrair definições de conexão de banco com mapeamento de tipo.

#### Scenario: Conexão SQL Server (Type=1)
**Given** uma CONNEXION com Type="1"
**When** o parser extrai a conexão
**Then** deve capturar name, source, database, user
**And** type_code deve ser 1
**And** database_type deve ser "sqlserver"
**And** driver_name deve ser "SQL Server"

#### Scenario: Conexão MySQL (Type=2)
**Given** uma CONNEXION com Type="2"
**When** o parser extrai a conexão
**Then** database_type deve ser "mysql"
**And** driver_name deve ser "MySQL"

#### Scenario: Conexão PostgreSQL (Type=3)
**Given** uma CONNEXION com Type="3"
**When** o parser extrai a conexão
**Then** database_type deve ser "postgresql"
**And** driver_name deve ser "PostgreSQL"

#### Scenario: Conexão Oracle (Type=4)
**Given** uma CONNEXION com Type="4"
**When** o parser extrai a conexão
**Then** database_type deve ser "oracle"
**And** driver_name deve ser "Oracle"

#### Scenario: Conexão HyperFile Classic (Type=5)
**Given** uma CONNEXION com Type="5"
**When** o parser extrai a conexão
**Then** database_type deve ser "hyperfile"
**And** driver_name deve ser "HyperFile Classic"

#### Scenario: Conexão HyperFile C/S (Type=6)
**Given** uma CONNEXION com Type="6"
**When** o parser extrai a conexão
**Then** database_type deve ser "hyperfile_cs"
**And** driver_name deve ser "HyperFile C/S"

#### Scenario: Tipo desconhecido (Type não mapeado)
**Given** uma CONNEXION com Type="99"
**When** o parser extrai a conexão
**Then** database_type deve ser "unknown"
**And** deve adicionar warning ao resultado

---

## ADDED Requirements

### Requirement: XDD-CONN-002 - Extract Extended Connection Info
O parser MUST extrair informações estendidas (INFOS_ETENDUES) da conexão.

#### Scenario: Extrair porta de INFOS_ETENDUES
**Given** uma CONNEXION com INFOS_ETENDUES contendo porta
**When** o parser extrai a conexão
**Then** deve extrair a porta da string INFOS_ETENDUES
**And** armazenar em connection.port

#### Scenario: Usar porta default quando não especificada
**Given** uma CONNEXION sem porta em INFOS_ETENDUES
**And** Type="1" (SQL Server)
**When** o parser extrai a conexão
**Then** connection.port deve ser "1433"

#### Scenario: Armazenar INFOS_ETENDUES completo
**Given** uma CONNEXION com INFOS_ETENDUES=";Initial Catalog=MyDB;Timeout=30"
**When** o parser extrai a conexão
**Then** connection.extended_info deve conter a string completa
**And** pode ser usada para parsing adicional pelo gerador

---

### Requirement: XDD-CONN-003 - Connection Tables Association
O parser MUST associar tabelas às suas conexões.

#### Scenario: Tabela com conexão específica
**Given** um FICHIER com Connexion="CNX_BASE_HOMOLOG"
**When** o parser extrai a tabela
**Then** table.connection_name deve ser "CNX_BASE_HOMOLOG"
**And** a conexão deve existir na lista de connections

#### Scenario: Tabela sem conexão especificada
**Given** um FICHIER sem atributo Connexion
**When** o parser extrai a tabela
**Then** table.connection_name deve ser ""
**And** deve usar a primeira conexão como default no gerador

---

### Requirement: STARTER-ENV-001 - Dynamic Environment Generation
O StarterKit MUST gerar .env.example baseado nas conexões extraídas.

#### Scenario: Gerar variáveis para conexão SQL Server
**Given** uma conexão com database_type="sqlserver"
**And** name="CNX_BASE"
**When** o StarterKit gera .env.example
**Then** deve incluir CNX_BASE_HOST, CNX_BASE_PORT, CNX_BASE_DATABASE
**And** CNX_BASE_USER, CNX_BASE_PASSWORD, CNX_BASE_TYPE

#### Scenario: Gerar para múltiplas conexões
**Given** duas conexões: "CNX_PRINCIPAL" (sqlserver) e "CNX_LOG" (mysql)
**When** o StarterKit gera .env.example
**Then** deve gerar variáveis separadas para cada conexão
**And** deve incluir comentário identificando cada seção

#### Scenario: Conexão HyperFile não suportada
**Given** uma conexão com database_type="hyperfile"
**When** o StarterKit gera .env.example
**Then** deve incluir comentário indicando que HyperFile requer tratamento especial
**And** não deve gerar connection string SQLAlchemy

---

### Requirement: STARTER-DB-001 - Multi-Connection Database Module
O StarterKit MUST gerar database.py com suporte a múltiplas conexões.

#### Scenario: Gerar inicialização de múltiplas conexões
**Given** conexões ["CNX_MAIN", "CNX_LOG"]
**When** o StarterKit gera database.py
**Then** deve gerar código que inicializa ambas as conexões
**And** deve armazenar em dict connections por nome

#### Scenario: Gerar get_db com seleção de conexão
**Given** múltiplas conexões configuradas
**When** o código gera get_db()
**Then** deve aceitar parâmetro connection_name opcional
**And** deve usar primeira conexão como default

---

### Requirement: STARTER-REQ-001 - Dynamic Requirements Generation
O StarterKit MUST gerar requirements.txt com drivers corretos.

#### Scenario: Incluir driver SQL Server
**Given** uma conexão com database_type="sqlserver"
**When** o StarterKit gera requirements.txt
**Then** deve incluir aioodbc>=1.0.0
**And** deve incluir sqlalchemy[asyncio]>=2.0.0

#### Scenario: Incluir driver PostgreSQL
**Given** uma conexão com database_type="postgresql"
**When** o StarterKit gera requirements.txt
**Then** deve incluir asyncpg>=0.29.0

#### Scenario: Incluir múltiplos drivers
**Given** conexões [sqlserver, mysql]
**When** o StarterKit gera requirements.txt
**Then** deve incluir aioodbc e aiomysql
**And** não deve duplicar sqlalchemy
