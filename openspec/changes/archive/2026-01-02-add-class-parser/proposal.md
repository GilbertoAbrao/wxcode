# Proposal: add-class-parser

## Why

O pipeline de parsing do wxcode precisa extrair estrutura de classes WinDev (.wdc) para:
1. Gerar classes Python equivalentes na conversão
2. Mapear herança e dependências entre classes
3. Identificar padrões de Domain Entities (ex: `_classBasic` como base de persistência)

Atualmente temos parsers para procedures (.wdg) e schema (.xdd), mas classes são essenciais pois:
- Contêm lógica de domínio (validação, cálculos)
- Definem herança e polimorfismo
- São base para geração de Pydantic models

## What Changes

### Novo Parser: `wdc_parser.py`
- Extrai definição de classe: nome, herança, abstract
- Extrai membros com visibilidade (PUBLIC, PRIVATE, PROTECTED)
- Extrai métodos (Constructor, Destructor, métodos normais)
- Extrai constantes da classe
- Identifica dependências (classes usadas, arquivos HyperFile)

### Novo Model: `ClassDefinition`
- Document Beanie para armazenar classes parseadas
- Embedded models: `ClassMember`, `ClassMethod`, `ClassConstant`
- Índices para busca por herança e dependências

### Novo CLI: `parse-classes`
- Comando para parsear classes de um projeto
- Idempotente (remove anterior antes de inserir)
- Exibe estatísticas e preview

## Spec Deltas
- `class-parsing`: Nova capability com requisitos de parsing
