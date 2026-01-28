# schema-parsing Specification

## Purpose
TBD - created by archiving change add-schema-parser. Update Purpose after archive.
## Requirements
### Requirement: XDD-DISCOVER-001 - Discover Analysis File
O sistema MUST descobrir o arquivo .xdd usando o analysis_path do projeto ou fallback automático.

#### Scenario: Descobrir via Project.analysis_path
**Given** um projeto com `analysis_path = ".\BD.ana\BD.wda"`
**When** o sistema busca o arquivo de Analysis
**Then** deve converter o path .wda para .xdd
**And** deve retornar o path `BD.ana/BD.xdd`

#### Scenario: Fallback quando analysis_path é null
**Given** um projeto com `analysis_path = null`
**And** o projeto contém `MeuApp/MinhaBase.ana/Schema.xdd`
**When** o sistema busca o arquivo de Analysis
**Then** deve fazer descoberta automática
**And** deve encontrar e retornar o path do arquivo .xdd

#### Scenario: Descobrir com nome customizado
**Given** um projeto com estrutura `MeuApp/MinhaBase.ana/Schema.xdd`
**When** o sistema busca o arquivo de Analysis
**Then** deve encontrar e retornar o path do arquivo .xdd
**And** o nome específico do arquivo não deve importar

#### Scenario: Múltiplos diretórios .ana
**Given** um projeto com múltiplos diretórios .ana
**When** o sistema busca o arquivo de Analysis
**Then** deve retornar o primeiro arquivo .xdd encontrado
**And** pode emitir warning sobre múltiplas Analysis

---

### Requirement: XDD-MAPPER-001 - Capture analysis_path in ProjectMapper
O ProjectMapper MUST capturar corretamente o analysis_path do arquivo .wwp/.wdp.

#### Scenario: Capturar analysis_path após configurations
**Given** um arquivo .wwp com `analysis : .\BD.ana\BD.wda` na linha 1982
**And** `configurations :` está na linha 13
**When** o ProjectMapper processa o arquivo
**Then** deve capturar `analysis_path = ".\BD.ana\BD.wda"`
**And** o Project salvo no MongoDB deve ter o campo preenchido

---

### Requirement: XDD-PARSE-001 - Parse Analysis File
O sistema MUST parsear arquivos .xdd (XML) e extrair todas as definições de banco.

#### Scenario: Parse arquivo .xdd válido
**Given** um arquivo .xdd no formato XML WinDev (qualquer nome)
**When** o XddParser processa o arquivo
**Then** deve extrair todas as conexões (CONNEXION)
**And** deve extrair todas as tabelas (FICHIER)
**And** deve extrair todas as colunas (RUBRIQUE) de cada tabela
**And** deve retornar XddParseResult com dados estruturados

#### Scenario: Arquivo com encoding ISO-8859-1
**Given** um arquivo .xdd com encoding ISO-8859-1
**When** o parser tenta ler o arquivo
**Then** deve detectar e converter corretamente o encoding
**And** caracteres acentuados devem ser preservados

---

### Requirement: XDD-TYPE-001 - Map HyperFile Types
O parser MUST mapear tipos HyperFile para tipos Python equivalentes.

#### Scenario: Mapear tipo Text (TYPE=2)
**Given** uma coluna com TYPE=2 e TAILLE=200
**When** o parser mapeia o tipo
**Then** python_type deve ser "str"
**And** size deve ser 200

#### Scenario: Mapear tipo Auto-increment (TYPE=24)
**Given** uma coluna com TYPE=24 e TYPE_CLE=1
**When** o parser mapeia o tipo
**Then** python_type deve ser "int"
**And** is_auto_increment deve ser True
**And** is_primary_key deve ser True

#### Scenario: Mapear tipo DateTime (TYPE=34)
**Given** uma coluna com TYPE=34
**When** o parser mapeia o tipo
**Then** python_type deve ser "datetime"

#### Scenario: Mapear tipo Decimal (TYPE=41)
**Given** uma coluna com TYPE=41 e TAILLE=5
**When** o parser mapeia o tipo
**Then** python_type deve ser "Decimal"

#### Scenario: Tipo desconhecido
**Given** uma coluna com TYPE=99 (não mapeado)
**When** o parser tenta mapear
**Then** python_type deve ser "Any"
**And** deve adicionar warning ao resultado

---

### Requirement: XDD-KEY-001 - Detect Keys and Indexes
O parser MUST identificar chaves primárias e índices.

#### Scenario: Detectar Primary Key (TYPE_CLE=1)
**Given** uma coluna com TYPE_CLE=1
**When** o parser analisa a coluna
**Then** is_primary_key deve ser True
**And** is_indexed deve ser True

#### Scenario: Detectar índice não-único (TYPE_CLE=2)
**Given** uma coluna com TYPE_CLE=2
**When** o parser analisa a coluna
**Then** is_primary_key deve ser False
**And** is_indexed deve ser True
**And** índice inferido deve ter is_unique=False

#### Scenario: Detectar índice único (TYPE_CLE=3)
**Given** uma coluna com TYPE_CLE=3
**When** o parser analisa a coluna
**Then** is_indexed deve ser True
**And** índice inferido deve ter is_unique=True

---

### Requirement: XDD-NULL-001 - Extract Nullable and Defaults
O parser MUST extrair informações de nullable e valores default.

#### Scenario: Coluna nullable
**Given** uma coluna com INDICERUBRIQUE Null="1"
**When** o parser analisa a coluna
**Then** nullable deve ser True

#### Scenario: Coluna NOT NULL
**Given** uma coluna com INDICERUBRIQUE Null="0"
**When** o parser analisa a coluna
**Then** nullable deve ser False

#### Scenario: Coluna com default
**Given** uma coluna com INDICERUBRIQUE Valeur="0"
**When** o parser analisa a coluna
**Then** default_value deve ser "0"

---

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

### Requirement: CLI-SCHEMA-001 - Parse Schema Command
O CLI MUST ter comando para parsear schema de um projeto.

#### Scenario: Executar parse-schema com sucesso
**Given** um projeto importado no MongoDB
**And** o projeto tem um diretório .ana com arquivo .xdd
**When** o usuário executa `wxcode parse-schema ./projeto`
**Then** deve encontrar e parsear o arquivo .xdd
**And** deve salvar DatabaseSchema no MongoDB
**And** deve exibir estatísticas (conexões, tabelas, colunas)

#### Scenario: Projeto sem Analysis
**Given** um diretório de projeto sem pasta .ana
**When** o usuário executa `wxcode parse-schema ./projeto`
**Then** deve exibir erro "Arquivo de Analysis (.xdd) não encontrado"

#### Scenario: Execução idempotente
**Given** um schema já existente para o projeto
**When** o usuário executa `parse-schema` novamente
**Then** deve deletar o schema anterior
**And** deve criar novo schema atualizado
**And** não deve duplicar dados

---

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

### Requirement: STARTER-CONFIG-001 - Dynamic Config Generation
O StarterKit MUST gerar config.py com campos de settings para cada conexão.

#### Scenario: Gerar settings para conexão SQL Server
**Given** uma conexão com name="CNX_BASE" e database_type="sqlserver"
**When** o StarterKit gera config.py
**Then** deve incluir campos cnx_base_host, cnx_base_port, cnx_base_database
**And** deve incluir campos cnx_base_user, cnx_base_password
**And** nomes devem ser lowercase

#### Scenario: Gerar settings para múltiplas conexões
**Given** conexões ["CNX_MAIN", "CNX_LOG"]
**When** o StarterKit gera config.py
**Then** deve gerar campos separados para cada conexão
**And** campos devem ter prefixo do nome da conexão em lowercase

#### Scenario: Config e Database sincronizados
**Given** conexões extraídas do .xdd
**When** o StarterKit gera config.py e database.py
**Then** todos os campos referenciados em database.py devem existir em config.py
**And** aplicação deve iniciar sem AttributeError

