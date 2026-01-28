# Proposal: fix-page-converter

## Summary

Corrigir PageConverter e StarterKit para gerar código válido que funciona sem intervenção manual.

## Problem Statement

Atualmente, ao converter páginas com `wxcode convert --layer route`, o código gerado **não funciona** por três razões:

1. **Conflito routers vs routes**: StarterKit gera `app/routes/__init__.py`, mas OutputWriter atualiza `app/routers/__init__.py`. O main.py importa de `app/routes`, mas os arquivos são gerados em `app/routers/`.

2. **StarterKit sobrescreve routers**: Cada execução do `convert` regenera o StarterKit, que sobrescreve `app/routes/__init__.py` com código comentado, removendo imports de páginas já convertidas.

3. **LLM gera imports inexistentes**: O código gerado pelo LLM inclui imports como `from app.models import ContaFitbank` ou `from app.services.auth import get_current_user` que não existem.

## Proposed Solution

### 1. Unificar em `app/routers/`

- StarterKit gera `app/routers/__init__.py` (não `routes`)
- main.py importa de `app.routers`
- OutputWriter já usa `app/routers/__init__.py` (manter)
- Remover pasta `app/routes/` do StarterKit

### 2. Preservar router includes existentes

- StarterKit verifica se `app/routers/__init__.py` já existe
- Se existir, preserva imports/includes existentes
- Apenas adiciona comentário se arquivo estiver vazio

### 3. Validar imports no código gerado

- Criar `ImportValidator` que analisa imports no código gerado
- Remover imports de módulos que não existem em `app/`
- Gerar stubs para dependências padrão (auth, models, etc.)

### 4. Gerar dependências padrão automaticamente

- Criar `app/services/auth.py` com `get_current_user` padrão
- Criar `app/core/security.py` com `create_access_token` padrão
- OutputWriter adiciona estas dependências automaticamente

## Impact

- **Files Modified**:
  - `src/wxcode/generator/starter_kit.py`
  - `src/wxcode/llm_converter/output_writer.py`

- **New Files**:
  - `src/wxcode/llm_converter/import_validator.py`

- **Breaking Changes**: Nenhum (melhoria de comportamento)

## Success Criteria

1. `wxcode convert Linkpay_ADM --layer schema` seguido de `--layer route -e PAGE_Login -e PAGE_PRINCIPAL` deve gerar código que roda sem erros de import
2. Regenerar o StarterKit não deve sobrescrever routers já configurados
3. Servidor inicia sem ImportError ou ModuleNotFoundError
