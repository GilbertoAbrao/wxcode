# page-converter-fixes Specification

## Purpose

Corrigir geração de código pelo PageConverter para produzir código válido sem intervenção manual.

## ADDED Requirements

### Requirement: Write generated files to project

O OutputWriter MUST escrever os arquivos gerados no projeto target e validar imports.

#### Scenario: Validar imports antes de escrever rota

**Given** código gerado com `from app.models import ContaFitbank`
**And** módulo `app.models.conta_fitbank` não existe

**When** OutputWriter.write(result) é executado

**Then** deve:
- Remover a linha de import inválido
- Logar warning: "Import removido: app.models.ContaFitbank (módulo não encontrado)"
- Escrever código sem o import inválido

#### Scenario: Preservar imports válidos

**Given** código gerado com `from app.services.auth import get_current_user`
**And** arquivo `app/services/auth.py` existe com função `get_current_user`

**When** OutputWriter.write(result) é executado

**Then** deve preservar o import no código escrito

#### Scenario: Preservar imports de stdlib e third-party

**Given** código gerado com:
- `from datetime import datetime`
- `from fastapi import APIRouter`
- `from sqlalchemy.orm import Session`

**When** OutputWriter.write(result) é executado

**Then** deve preservar todos os imports (não são de `app.`)

---

### Requirement: Atualizar router __init__.py corretamente

O OutputWriter MUST atualizar `app/routers/__init__.py` (não `app/routes/`).

#### Scenario: Atualizar routers/__init__.py

**Given** nova rota criada para "login" em `app/routers/login.py`

**When** os arquivos são escritos

**Then** deve atualizar `app/routers/__init__.py` para incluir:
```python
from .login import router as login_router
router.include_router(login_router, tags=["login"])
```

#### Scenario: Não duplicar imports existentes

**Given** `app/routers/__init__.py` já tem `from .login import router as login_router`

**When** PAGE_Login é convertida novamente

**Then** não deve adicionar import duplicado

---

### Requirement: StarterKit preserva routers existentes

O StarterKit MUST preservar `app/routers/__init__.py` se já tiver imports ativos.

#### Scenario: Preservar arquivo com imports

**Given** `app/routers/__init__.py` contém:
```python
from .login import router as login_router
router.include_router(login_router)
```

**When** StarterKit.generate() é executado

**Then** não deve sobrescrever o arquivo

#### Scenario: Sobrescrever arquivo vazio

**Given** `app/routers/__init__.py` contém apenas:
```python
"""Routers package."""
from fastapi import APIRouter
router = APIRouter()
# comentários...
```

**When** StarterKit.generate() é executado

**Then** pode sobrescrever com template atualizado

---

### Requirement: StarterKit gera dependências auth padrão

O StarterKit MUST gerar arquivos de autenticação padrão.

#### Scenario: Gerar auth service

**When** StarterKit.generate() é executado

**Then** deve criar `app/services/auth.py` com:
- Classe `CurrentUser`
- Função `async def get_current_user(request: Request)`

#### Scenario: Gerar security utils

**When** StarterKit.generate() é executado

**Then** deve criar `app/core/security.py` com:
- Função `create_access_token(data: dict)`

#### Scenario: Não sobrescrever auth existente

**Given** `app/services/auth.py` já existe com conteúdo customizado

**When** StarterKit.generate() é executado

**Then** não deve sobrescrever o arquivo existente

---

### Requirement: ImportValidator valida código gerado

O ImportValidator MUST validar e corrigir imports no código gerado.

#### Scenario: Remover import de módulo inexistente

**Given** código com `from app.models import ContaFitbank`
**And** não existe `app/models/conta_fitbank.py` nem export em `app/models/__init__.py`

**When** ImportValidator.validate_and_fix(code) é executado

**Then** deve retornar:
- Código sem a linha de import
- Lista `["app.models.ContaFitbank"]` de imports removidos

#### Scenario: Detectar módulos existentes

**Given** estrutura:
```
app/
├── services/
│   ├── __init__.py
│   └── auth.py (contém get_current_user)
└── models/
    └── __init__.py (vazio)
```

**When** ImportValidator escaneia `app/`

**Then** deve detectar:
- `app.services.auth` como módulo válido
- `app.models` como módulo válido (mas sem exports)
