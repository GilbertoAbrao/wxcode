# Spec: Schema Generator

## Overview

Gerador de Pydantic models a partir do DatabaseSchema extraído de projetos WinDev.

## ADDED Requirements

### Requirement: Generate Pydantic models from database tables

O sistema MUST gerar um arquivo Pydantic model para cada tabela do schema.

#### Scenario: Tabela simples com tipos básicos

**Given** um DatabaseSchema com tabela CLIENTE contendo:
- id (AutoIncrement)
- nome (Text)
- email (Text)
- ativo (Boolean)
- data_cadastro (DateTime)

**When** SchemaGenerator.generate() é executado

**Then** deve gerar arquivo `app/models/cliente.py` com:
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Cliente(BaseModel):
    id: int
    nome: str
    email: str
    ativo: bool
    data_cadastro: datetime

    class Config:
        from_attributes = True
```

#### Scenario: Campos nullable

**Given** uma tabela com campo `observacao` que permite NULL

**When** o model é gerado

**Then** o campo deve ser `observacao: Optional[str] = None`

#### Scenario: Campo com valor default

**Given** uma tabela com campo `status` com default "ATIVO"

**When** o model é gerado

**Then** o campo deve ser `status: str = "ATIVO"`

---

### Requirement: Map HyperFile types to Python types correctly

O sistema MUST mapear todos os tipos HyperFile para tipos Python corretos.

#### Scenario: Tipo Integer (code 4)

**Given** uma coluna com hyperfile_type = 4

**When** o tipo Python é determinado

**Then** deve retornar `int`

#### Scenario: Tipo Currency (code 14)

**Given** uma coluna com hyperfile_type = 14

**When** o tipo Python é determinado

**Then** deve retornar `Decimal` com import de `decimal`

#### Scenario: Tipo UUID (code 26)

**Given** uma coluna com hyperfile_type = 26

**When** o tipo Python é determinado

**Then** deve retornar `UUID` com import de `uuid`

---

### Requirement: Generate __init__.py with all model exports

O sistema MUST gerar um __init__.py que exporta todos os models.

#### Scenario: Múltiplas tabelas

**Given** um schema com tabelas CLIENTE, PEDIDO, PRODUTO

**When** a geração é concluída

**Then** deve gerar `app/models/__init__.py` com:
```python
from .cliente import Cliente
from .pedido import Pedido
from .produto import Produto

__all__ = ["Cliente", "Pedido", "Produto"]
```

---

### Requirement: Detect and annotate relationships

O sistema MUST detectar relacionamentos entre tabelas e adicionar anotações.

#### Scenario: Foreign key detectada por nome

**Given** uma tabela PEDIDO com campo `cliente_id`

**When** o model é gerado

**Then** deve incluir comentário indicando relacionamento:
```python
cliente_id: int  # FK: CLIENTE.id
```

#### Scenario: Relacionamento inferido de binding

**Given** um controle com data_binding `PEDIDO.cliente_id → CLIENTE.id`

**When** o model é gerado

**Then** deve adicionar o relacionamento detectado

---

### Requirement: Add basic validators for special fields

O sistema MUST adicionar validadores para campos especiais.

#### Scenario: Campo email

**Given** uma coluna com nome contendo "email"

**When** o model é gerado

**Then** deve incluir validador:
```python
from pydantic import EmailStr

email: EmailStr
```

#### Scenario: Campo CPF

**Given** uma coluna com nome contendo "cpf"

**When** o model é gerado

**Then** deve incluir comentário TODO para validador:
```python
cpf: str  # TODO: Add CPF validator
```
