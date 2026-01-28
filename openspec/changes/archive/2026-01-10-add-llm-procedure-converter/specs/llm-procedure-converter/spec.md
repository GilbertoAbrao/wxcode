# llm-procedure-converter Specification

## Purpose

Conversão de procedure groups (.wdg) para services Python usando LLM, com a mesma qualidade de código que o PageConverter gera para páginas.

## ADDED Requirements

### Requirement: Build procedure context from MongoDB

O ProcedureContextBuilder MUST construir contexto completo de um procedure group.

#### Scenario: Grupo com múltiplas procedures

**Given** um Element "ServerProcedures.wdg" com procedures:
- Global_FazLoginUsuarioInterno(sLogin, sSenha): string
- Global_SetaTempoSessao()
- Global_LogProcesso(sProcesso, sStatus, sDetalhes)

**When** ProcedureContextBuilder.build(element_id) é executado

**Then** deve retornar ProcedureContext com:
- group_name: "ServerProcedures"
- procedures: lista com código completo das 3 procedures
- referenced_procedures: procedures de outros grupos chamadas
- estimated_tokens: número estimado de tokens

#### Scenario: Procedures com dependências externas

**Given** procedure `Global_FazLoginUsuarioInterno` que chama `Util_FormatarData` de outro grupo

**When** o contexto é construído

**Then** deve incluir `Util_FormatarData` em referenced_procedures com seu código

---

### Requirement: Convert procedure group via LLM

O ProcedureConverter MUST converter um procedure group completo para service Python.

#### Scenario: Conversão de grupo simples

**Given** procedure group "ServerProcedures" com 3 procedures

**When** ProcedureConverter.convert(element_id) é executado

**Then** deve:
1. Construir contexto com ProcedureContextBuilder
2. Chamar LLM com prompt específico para procedures
3. Parsear resposta como service Python
4. Escrever arquivo app/services/server_service.py
5. Retornar ProcedureConversionResult com métricas

#### Scenario: Dry run sem escrita

**Given** dry_run=True

**When** a conversão é executada

**Then** deve executar todos os passos exceto escrita de arquivos

---

### Requirement: Generate async Python service class

O LLM MUST gerar classe de service Python async com type hints.

#### Scenario: Procedure com parâmetros tipados

**Given** procedure:
```wlanguage
PROCEDURE Global_FazLoginUsuarioInterno(sLogin, sSenha): string
```

**When** convertida

**Then** deve gerar:
```python
async def global_faz_login_usuario_interno(
    self,
    s_login: str,
    s_senha: str
) -> str:
```

#### Scenario: Procedure com query SQL

**Given** procedure com HExecuteSQLQuery

**When** convertida

**Then** deve gerar código MongoDB equivalente usando motor/pymongo

#### Scenario: Procedure com tratamento de erro

**Given** procedure com CASE ERROR

**When** convertida

**Then** deve gerar try/except Python apropriado

---

### Requirement: Parse LLM response for service

O ServiceResponseParser MUST parsear resposta JSON do LLM.

#### Scenario: Resposta válida

**Given** resposta JSON:
```json
{
  "class_name": "ServerService",
  "filename": "server_service.py",
  "imports": ["from typing import Any"],
  "code": "class ServerService:..."
}
```

**When** ServiceResponseParser.parse() é executado

**Then** deve retornar ServiceConversionResult com todos os campos

#### Scenario: Validação de sintaxe Python

**Given** resposta com código Python

**When** parseado

**Then** deve validar sintaxe com ast.parse() antes de retornar

---

### Requirement: CLI support for service conversion

O CLI MUST suportar conversão de services via flag --layer.

#### Scenario: Converter apenas services

**Given** comando: `wxcode convert PROJECT --layer service -o ./output`

**When** executado

**Then** deve:
- Buscar elements do tipo procedure_group
- Converter cada grupo via LLM
- Gerar arquivos em app/services/

#### Scenario: Converter elemento específico

**Given** comando: `wxcode convert PROJECT --layer service -e ServerProcedures`

**When** executado

**Then** deve converter apenas o grupo ServerProcedures

#### Scenario: Converter tudo

**Given** comando: `wxcode convert PROJECT --layer all`

**When** executado

**Then** deve converter pages E services
