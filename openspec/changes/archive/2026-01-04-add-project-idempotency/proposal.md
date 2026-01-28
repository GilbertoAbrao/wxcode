# Change: Implementar Idempotência de Projetos e Purge Completo

## Why

O sistema atual permite criar múltiplos projetos com o mesmo nome, causando inconsistência de dados e dificultando a reimportação. Além disso, o delete de projetos não remove todas as collections dependentes (Control, Procedure, ClassDefinition, DatabaseSchema), deixando dados órfãos no banco.

## What Changes

1. **Unique Constraint no Nome do Projeto**
   - Adicionar índice único no campo `name` do model `Project`
   - Garantir que não existam dois projetos com o mesmo nome

2. **Verificação no Import**
   - Antes de criar um novo projeto, verificar se já existe um com o mesmo nome
   - Se existir, perguntar ao usuário se deseja sobrescrever (purge + reimport)
   - Comportamento via CLI com flag `--force` para sobrescrever sem confirmar

3. **Comando Purge Completo**
   - Novo comando CLI: `wxcode purge <project_name>`
   - Remove TODAS as collections dependentes do projeto:
     - Element
     - Control
     - Procedure
     - ClassDefinition
     - DatabaseSchema
     - Conversion
   - Atualizar endpoint DELETE da API para usar a mesma lógica

## Impact

- Affected specs: `project-management` (nova capability)
- Affected code:
  - `src/wxcode/models/project.py` - adicionar índice único
  - `src/wxcode/parser/project_mapper.py` - verificação de existência
  - `src/wxcode/cli.py` - novo comando purge e flag --force no import
  - `src/wxcode/api/projects.py` - atualizar cascade delete
