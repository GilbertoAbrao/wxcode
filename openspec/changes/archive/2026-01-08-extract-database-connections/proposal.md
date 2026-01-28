# Proposal: extract-database-connections

## Summary

Extrair e mapear conexões de banco de dados dos arquivos .xdd (Analysis WinDev) para que o starter kit gere `.env.example` correto baseado nas conexões reais da aplicação, suportando múltiplas conexões de tipos diferentes (SQL Server, MySQL, PostgreSQL, Oracle, HyperFile).

## Problem

Atualmente:
1. O `xdd_parser.py` extrai conexões mas armazena apenas `type_code: int` sem mapear para tipo de banco de dados
2. O `SchemaConnection` não tem campo `database_type` para armazenar o tipo mapeado
3. O `starter_kit.py` gera `.env.example` com URL hardcoded para MongoDB (base do wxcode) em vez de usar as conexões reais da aplicação
4. Aplicações WinDev podem ter múltiplas conexões de tipos diferentes (ex: SQL Server para dados + HyperFile para logs)

## Solution

1. **Mapear Type codes do .xdd para tipos de banco de dados conhecidos**
   - Type=1 → SQL Server (Native Access)
   - Type=2 → MySQL (Native Access)
   - Type=3 → PostgreSQL (Native Access)
   - Type=4 → Oracle (Native Access)
   - Type=5 → HyperFile Classic
   - Type=6 → HyperFile Client/Server
   - (outros tipos conforme documentação PCSoft)

2. **Adicionar campo `database_type` ao SchemaConnection**
   - `database_type: str` com valores como "sqlserver", "mysql", "postgresql", "oracle", "hyperfile"

3. **Atualizar starter kit para gerar `.env.example` dinâmico**
   - Gerar variáveis de ambiente para cada conexão encontrada
   - Usar formato de connection string apropriado para cada tipo

4. **Atualizar database.py para suportar múltiplas conexões**
   - Registrar conexões com nomes específicos
   - Gerar código de inicialização apropriado

## Scope

- **In scope:**
  - Mapeamento de Type codes para tipos de banco
  - Atualização do model SchemaConnection
  - Geração de .env.example dinâmico
  - Suporte a múltiplas conexões no database.py gerado

- **Out of scope:**
  - Migração de dados entre bancos
  - Conversão de queries específicas por banco
  - Suporte a conexões ODBC genéricas

## Related Specs

- `schema-parsing` - Adição de novos requirements para mapeamento de tipos de conexão
