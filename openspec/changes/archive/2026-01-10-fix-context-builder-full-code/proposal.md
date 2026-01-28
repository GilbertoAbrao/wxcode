# Proposal: fix-context-builder-full-code

## Problem

O LLM converter não está recebendo o código completo dos eventos e procedures, resultando em código gerado incompleto (stubs com TODO ao invés de lógica real).

### Evidências

1. **Truncamento de código de eventos**: Em `base.py:167-170`, o código dos eventos é truncado para 100 caracteres:
   ```python
   code_preview = code.strip()[:100]
   if len(code.strip()) > 100:
       code_preview += "..."
   ```

2. **Procedures globais não carregadas**: O `ContextBuilder` carrega apenas procedures locais (`is_local: True`), mas procedures globais referenciadas (como `Local_Login` que contém a lógica de autenticação) não são incluídas.

3. **Resultado**: O LLM gera stubs com `# TODO: Implementar` porque não recebe a lógica original.

## Solution

### 1. Remover truncamento de código de eventos

Modificar `base.py:_format_control()` para incluir o código completo dos eventos em um bloco de código formatado.

### 2. Carregar procedures referenciadas

Modificar `ContextBuilder` para:
- Extrair nomes de procedures chamadas nos eventos
- Buscar essas procedures no MongoDB (globais do projeto)
- Incluí-las no contexto enviado ao LLM

### 3. Manter limite de tokens

Adicionar lógica para priorizar código mais relevante se o contexto exceder o limite de tokens:
1. Código de eventos (sempre incluir)
2. Procedures chamadas diretamente
3. Procedures de segundo nível (chamadas por procedures diretas)

## Impact

- **Arquivos modificados**: 2
  - `src/wxcode/llm_converter/providers/base.py`
  - `src/wxcode/llm_converter/context_builder.py`

- **Breaking changes**: Nenhum (apenas melhora a qualidade do contexto)

- **Riscos**:
  - Aumento no uso de tokens (custo maior por conversão)
  - Mitigação: usar token_limit existente para priorizar

## Success Criteria

- [ ] Código de eventos é passado completo ao LLM
- [ ] Procedures globais referenciadas são incluídas no contexto
- [ ] Login gerado inclui lógica de autenticação (não apenas stubs)
- [ ] Limite de tokens é respeitado com priorização inteligente
