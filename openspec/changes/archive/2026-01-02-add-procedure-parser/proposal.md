# Change: Add Procedure Parser for .wdg files

## Why
O projeto wxcode precisa parsear arquivos .wdg (grupos de procedures WinDev) para extrair procedures server-side, suas assinaturas, parâmetros, tipos de retorno e código WLanguage. Isso é essencial para a fase de conversão da camada Business Logic (Fase 4.3 do pipeline).

Atualmente, os elementos .wdg são importados pelo project_mapper mas não têm seu conteúdo parseado para extração de procedures individuais.

## What Changes
- Criar `WdgParser` em `src/wxcode/parser/wdg_parser.py`
- Criar model `Procedure` em `src/wxcode/models/procedure.py`
- Extrair procedures individuais de arquivos .wdg
- Armazenar procedures no MongoDB com referência ao elemento pai
- Extrair: nome, parâmetros, tipo de retorno, código, dependências

## Impact
- Affected specs: `procedure-parsing` (novo)
- Affected code:
  - `src/wxcode/parser/wdg_parser.py` (novo)
  - `src/wxcode/models/procedure.py` (novo)
  - `src/wxcode/models/__init__.py` (export)
  - `src/wxcode/cli.py` (comando parse-procedures)
