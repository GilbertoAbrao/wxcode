# Spec: Service Generator

## Overview

Gerador de services FastAPI a partir de Procedures extraídas de arquivos .wdg.

## ADDED Requirements

### Requirement: Generate service classes from procedure groups

O sistema MUST gerar uma classe de service para cada grupo de procedures.

#### Scenario: Procedure group simples

**Given** um Element "ServerProcedures.wdg" com procedures:
- ValidarLogin(sUsuario, sSenha): boolean
- BuscarCliente(nId): JSON
- SalvarCliente(jsCliente is JSON): boolean

**When** ServiceGenerator.generate() é executado

**Then** deve gerar arquivo `app/services/server_procedures.py` com:
```python
from typing import Any

class ServerProceduresService:
    """Service convertido de ServerProcedures.wdg"""

    def __init__(self, db):
        self.db = db

    async def validar_login(self, s_usuario: str, s_senha: str) -> bool:
        ...

    async def buscar_cliente(self, n_id: int) -> dict:
        ...

    async def salvar_cliente(self, js_cliente: dict) -> bool:
        ...
```

#### Scenario: Múltiplos procedure groups

**Given** 3 elementos do tipo PROCEDURE_GROUP

**When** o gerador é executado

**Then** deve gerar 3 arquivos de service, um para cada grupo

---

### Requirement: Convert procedure parameters to typed arguments

O sistema MUST converter parâmetros WLanguage para argumentos Python tipados.

#### Scenario: Parâmetro string

**Given** parâmetro `sNome is string`

**When** convertido

**Then** deve gerar `s_nome: str`

#### Scenario: Parâmetro JSON

**Given** parâmetro `jsData is JSON`

**When** convertido

**Then** deve gerar `js_data: dict`

#### Scenario: Parâmetro com default

**Given** parâmetro `nLimit is int = 100`

**When** convertido

**Then** deve gerar `n_limit: int = 100`

#### Scenario: Parâmetro LOCAL

**Given** parâmetro `LOCAL sTemp is string`

**When** convertido

**Then** NÃO deve aparecer na assinatura (é variável local)

---

### Requirement: Convert H* functions using catalog

O sistema MUST converter funções H* usando o catálogo hyperfile_catalog.py.

#### Scenario: HAdd simples

**Given** código:
```wlanguage
CLIENTE.nome = sNome
CLIENTE.email = sEmail
HAdd(CLIENTE)
```

**When** convertido

**Then** deve gerar:
```python
await self.db.cliente.insert_one({
    "nome": s_nome,
    "email": s_email
})
```

#### Scenario: Loop HReadFirst/HReadNext

**Given** código:
```wlanguage
HReadFirst(CLIENTE, NOME)
WHILE NOT HOut(CLIENTE)
    ArrayAdd(arrClientes, CLIENTE.nome)
    HReadNext(CLIENTE, NOME)
END
```

**When** convertido

**Then** deve gerar:
```python
arr_clientes = []
async for doc in self.db.cliente.find().sort("nome"):
    arr_clientes.append(doc["nome"])
```

#### Scenario: HModify

**Given** código:
```wlanguage
HReadSeekFirst(CLIENTE, ID, nId)
IF HFound(CLIENTE) THEN
    CLIENTE.status = "INATIVO"
    HModify(CLIENTE)
END
```

**When** convertido

**Then** deve gerar:
```python
result = await self.db.cliente.update_one(
    {"id": n_id},
    {"$set": {"status": "INATIVO"}}
)
```

---

### Requirement: Preserve error handling

O sistema MUST preservar tratamento de erros.

#### Scenario: CASE ERROR

**Given** código com:
```wlanguage
CASE ERROR:
    RESULT {"error": ErrorInfo()}
END
```

**When** convertido

**Then** deve gerar:
```python
except Exception as e:
    return {"error": str(e)}
```

---

### Requirement: Convert procedure calls to method calls

O sistema MUST converter chamadas a outras procedures.

#### Scenario: Chamada interna ao mesmo grupo

**Given** código: `ValidarPermissao(sUsuario)`

**When** convertido e ValidarPermissao está no mesmo grupo

**Then** deve gerar: `await self.validar_permissao(s_usuario)`

#### Scenario: Chamada a outro grupo

**Given** código: `UtilService.FormatarData(dData)`

**When** convertido

**Then** deve gerar:
```python
# TODO: Import and inject UtilService
await self.util_service.formatar_data(d_data)
```
