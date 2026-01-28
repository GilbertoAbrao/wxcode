# Proposal: fix-config-connection-settings

## Why

O `StarterKitGenerator` gera `database.py` com referências a settings de conexão (ex: `settings.cnx_base_homolog_user`) mas não atualiza `config.py` para incluir esses campos. Isso causa erro ao iniciar a aplicação gerada.

## What Changes

1. Atualizar `_generate_config_py()` no `starter_kit.py` para gerar campos de configuração baseados nas conexões extraídas do .xdd
2. Cada conexão deve gerar campos: `{name}_host`, `{name}_port`, `{name}_database`, `{name}_user`, `{name}_password`

## Example

**Antes (bugado):**
```python
class Settings(BaseSettings):
    database_url: str = "mongodb://localhost:27017"  # Não usado
```

**Depois (correto):**
```python
class Settings(BaseSettings):
    # CNX_BASE_HOMOLOG
    cnx_base_homolog_host: str = "192.168.10.13"
    cnx_base_homolog_port: str = "1433"
    cnx_base_homolog_database: str = "Sipbackoffice_Virtualpay"
    cnx_base_homolog_user: str = "infiniti_all"
    cnx_base_homolog_password: str = ""

    # BdInfiniti
    bdinfiniti_host: str = "192.168.10.13"
    ...
```

## Scope

- **In scope:** Corrigir geração de `config.py` para incluir settings de conexão
- **Out of scope:** Outras melhorias no starter kit

## Related Specs

- `schema-parsing` (STARTER-ENV-001, STARTER-DB-001)
