# schema-parsing Spec Delta

## ADDED Requirements

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
