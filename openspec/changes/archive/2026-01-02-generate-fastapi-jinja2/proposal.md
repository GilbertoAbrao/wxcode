# Proposal: generate-fastapi-jinja2

## Summary

Implementar o gerador de código FastAPI + Jinja2 que transforma a Knowledge Base de projetos WinDev/WebDev em uma aplicação Python funcional.

## Motivation

O wxcode já possui uma Knowledge Base completa com:
- Schema do banco de dados (tabelas, colunas, índices)
- Classes de domínio (membros, métodos, herança)
- Procedures (parâmetros, código, dependências)
- Páginas (controles, eventos, bindings)
- Queries (SQL, parâmetros)
- Grafo de dependências (ordem topológica)

Falta o gerador que transforma esse conhecimento em código Python executável.

## Scope

### In Scope

1. **Schema Generator**: Gera Pydantic models a partir do DatabaseSchema
2. **Domain Generator**: Gera classes Python a partir de ClassDefinition
3. **Service Generator**: Gera services FastAPI a partir de Procedures
4. **Route Generator**: Gera rotas FastAPI a partir de Elements do tipo REST_API
5. **Template Generator**: Gera templates Jinja2 a partir de páginas
6. **CLI Integration**: Comando `wxcode generate` para orquestrar geração

### Out of Scope

- Geração de MCP Servers (será outra proposal)
- Geração de AI Agents (será outra proposal)
- Conversão de código WLanguage via LLM (usa catálogo H* e patterns)
- Validação/testes do código gerado (será FASE 5)

## Capabilities

### CAP-1: Schema Generator
Gera Pydantic models a partir do schema do banco:
- Um arquivo `models/<table_name>.py` por tabela
- Tipos Python corretos baseados no tipo HyperFile
- Relacionamentos via Foreign Keys (quando detectados)
- Validadores Pydantic para constraints

### CAP-2: Domain Generator
Gera classes Python a partir de classes WinDev:
- Preserva herança (inherits_from)
- Converte membros para atributos tipados
- Converte métodos para métodos Python
- Preserva constantes como class attributes

### CAP-3: Service Generator
Gera services a partir de procedures:
- Um service por grupo de procedures (.wdg)
- Converte funções H* usando catálogo `hyperfile_catalog.py`
- Preserva lógica de negócio
- Adiciona type hints baseados nos parâmetros

### CAP-4: Route Generator
Gera rotas FastAPI a partir de APIs REST:
- Endpoints com decorators corretos (@router.get, @router.post, etc)
- Request/Response models
- Dependency injection para services

### CAP-5: Template Generator
Gera templates Jinja2 a partir de páginas:
- Estrutura HTML baseada nos controles
- Formulários com campos corretos
- Tabelas com colunas baseadas em bindings
- Herança de templates (base.html)

## Success Criteria

- [ ] `wxcode generate <projeto> --output ./output` gera estrutura completa
- [ ] Código gerado é válido (sem erros de sintaxe Python)
- [ ] Models Pydantic refletem schema do banco
- [ ] Services contêm lógica das procedures
- [ ] Templates renderizam sem erros Jinja2
- [ ] Testes unitários para cada generator

## Dependencies

- Depende de: Knowledge Base completa (FASES 1-3 ✅)
- Usa: `hyperfile_catalog.py` para conversão de funções H*
- Usa: Models existentes (DatabaseSchema, ClassDefinition, Procedure, Element, Control)

## Risks

| Risco | Mitigação |
|-------|-----------|
| Código WLanguage muito complexo | Usar catálogo H* + markers para revisão manual |
| Relacionamentos não detectados | Inferir de bindings e queries |
| Templates muito simples | Iterar com projeto de referência |

## References

- `docs/ROADMAP.md` - Seção "Visão Estratégica" e prompts 4.1-4.5
- `src/wxcode/transpiler/hyperfile_catalog.py` - Catálogo de funções H*
- `docs/wlanguage/hyperfile-buffer.md` - Padrões de conversão buffer
