# Tasks: add-project-idempotency

## 1. Unique Constraint no Model Project

- [x] 1.1 Adicionar índice único no campo `name` em `Project.Settings.indexes` em `src/wxcode/models/project.py`
- [x] 1.2 Criar migration/script para verificar projetos duplicados existentes no banco (informativo)

## 2. Serviço de Purge

- [x] 2.1 Criar `src/wxcode/services/project_service.py` com função `purge_project(project_id)` que remove todas collections dependentes:
  - Element
  - Control
  - Procedure
  - ClassDefinition
  - DatabaseSchema
  - Conversion
  - Neo4j nodes (opcional, se disponível)
- [x] 2.2 Retornar estatísticas de quantos documentos foram removidos de cada collection

## 3. Comando CLI Purge

- [x] 3.1 Adicionar comando `wxcode purge <project_name>` em `src/wxcode/cli.py`
- [x] 3.2 Implementar confirmação interativa antes de purgar (com opção `--yes` para skip)
- [x] 3.3 Exibir estatísticas de remoção ao final

## 4. Verificação no Import

- [x] 4.1 Modificar `ProjectElementMapper.map()` em `src/wxcode/parser/project_mapper.py` para verificar se projeto existe antes de criar
- [x] 4.2 Adicionar flag `--force` ao comando `import` que faz purge automático se projeto existir
- [x] 4.3 Sem `--force`, exibir erro e sugerir usar `--force` quando projeto já existir

## 5. Atualizar API

- [x] 5.1 Modificar `delete_project()` em `src/wxcode/api/projects.py` para usar `purge_project()` do service
- [x] 5.2 Retornar estatísticas de remoção na resposta

## 6. Testes

- [x] 6.1 Criar `tests/test_project_idempotency.py` com testes para:
  - Unique constraint impede duplicatas
  - Import com projeto existente falha sem --force
  - Import com --force faz purge e reimporta
  - Purge remove todas as collections
  - API delete remove todas as collections
