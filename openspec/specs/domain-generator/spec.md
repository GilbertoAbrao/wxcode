# domain-generator Specification

## Purpose
TBD - created by archiving change generate-fastapi-jinja2. Update Purpose after archive.
## Requirements
### Requirement: Generate Python classes from ClassDefinition

O sistema MUST gerar classes Python preservando estrutura das classes WinDev.

#### Scenario: Classe simples com membros

**Given** uma ClassDefinition "classUsuario" com membros:
- sNome: string (public)
- sEmail: string (public)
- nId: int (private)

**When** DomainGenerator.generate() é executado

**Then** deve gerar arquivo `app/domain/class_usuario.py` com:
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ClassUsuario:
    """Classe convertida de classUsuario.wdc"""

    s_nome: str = ""
    s_email: str = ""
    _n_id: int = 0  # private
```

#### Scenario: Classe com herança

**Given** uma ClassDefinition "classAdmin" que herda de "classUsuario"

**When** o gerador é executado

**Then** deve gerar:
```python
from .class_usuario import ClassUsuario

@dataclass
class ClassAdmin(ClassUsuario):
    """Classe convertida de classAdmin.wdc"""

    # membros adicionais
```

#### Scenario: Classe abstrata

**Given** uma ClassDefinition com is_abstract = True

**When** o gerador é executado

**Then** deve gerar classe com ABC:
```python
from abc import ABC, abstractmethod

class ClassBase(ABC):
    """Classe abstrata convertida de classBase.wdc"""
```

---

### Requirement: Convert methods preserving signatures

O sistema MUST converter métodos preservando assinaturas e parâmetros.

#### Scenario: Método simples sem retorno

**Given** um método "Salvar()" sem parâmetros e sem retorno

**When** o método é convertido

**Then** deve gerar:
```python
async def salvar(self) -> None:
    """
    Método convertido de WLanguage.

    Original: PROCEDURE Salvar()
    """
    # TODO: Implement method logic
    pass
```

#### Scenario: Método com parâmetros tipados

**Given** um método "Buscar(sNome is string, nLimit is int = 10): JSON"

**When** o método é convertido

**Then** deve gerar:
```python
async def buscar(self, s_nome: str, n_limit: int = 10) -> dict:
    """
    Original: PROCEDURE Buscar(sNome is string, nLimit is int = 10): JSON
    """
    pass
```

#### Scenario: Constructor

**Given** um método com type_code = 27 (constructor)

**When** o método é convertido

**Then** deve gerar `__init__` ou `__post_init__` para dataclass

---

### Requirement: Preserve constants as class attributes

O sistema MUST preservar constantes como atributos de classe.

#### Scenario: Constantes numéricas

**Given** uma ClassDefinition com constantes:
- STATUS_ATIVO = 1
- STATUS_INATIVO = 0

**When** o gerador é executado

**Then** deve gerar:
```python
class ClassStatus:
    STATUS_ATIVO: int = 1
    STATUS_INATIVO: int = 0
```

---

### Requirement: Convert method bodies using H* catalog

O sistema MUST converter o código dos métodos usando o catálogo de funções H*.

#### Scenario: Método com HReadSeekFirst

**Given** um método com código:
```wlanguage
HReadSeekFirst(CLIENTE, NOME, sNomeBusca)
IF HFound(CLIENTE) THEN
    RESULT True
END
RESULT False
```

**When** o código é convertido

**Then** deve gerar:
```python
async def buscar_cliente(self, s_nome_busca: str) -> bool:
    result = await self.db.cliente.find_one({"nome": s_nome_busca})
    if result:
        return True
    return False
```

#### Scenario: Método com função needs_llm

**Given** um método com HExecuteQuery (marcado needs_llm=True no catálogo)

**When** o código é convertido

**Then** deve gerar TODO marker:
```python
async def executar_query(self) -> None:
    # TODO: [WXCODE] Manual conversion required
    # Original: HExecuteQuery(QRY_COMPLEX, hQueryDefault, param)
    # Reason: HExecuteQuery requires SQL analysis
    raise NotImplementedError()
```

