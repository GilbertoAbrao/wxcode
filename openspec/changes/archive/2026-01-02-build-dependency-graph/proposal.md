# Proposal: build-dependency-graph

## Summary
Implementar o analisador de dependências (Fase 3.1) que constrói um grafo de relacionamentos entre todos os elementos do projeto WinDev e calcula a ordem topológica para conversão.

## Motivation
A conversão de projetos WinDev DEVE seguir ordem topológica para respeitar dependências:
1. **Schema** (tabelas) → Classes dependem de tabelas
2. **Domain** (classes base) → Classes derivadas dependem de classes pai
3. **Business** (procedures) → Procedures chamam outras procedures e usam classes
4. **API** (endpoints) → Endpoints usam procedures e classes
5. **UI** (páginas) → Páginas usam tudo acima

Sem ordem correta, a conversão gerará código com referências quebradas.

## Current State
- **Dados disponíveis no MongoDB:**
  - 14 classes com `dependencies.uses_classes` (herança)
  - 371 procedures com `dependencies.calls_procedures` e `dependencies.uses_files`
  - 366 elements com `dependencies.uses` e `dependencies.data_files`
  - 1 schema com tabelas do banco

- **Estruturas existentes:**
  - `Element.dependencies` (ElementDependencies)
  - `Element.topological_order` (int, não preenchido)
  - `Element.layer` (ElementLayer enum)
  - `ClassDefinition.dependencies` (ClassDependencies)
  - `Procedure.dependencies` (ProcedureDependencies)

- **Diretório `analyzer/`:** Vazio (apenas `__init__.py`)

## Proposed Solution

### 1. DependencyGraph Class
Classe principal que:
- Carrega todos os elementos do MongoDB (classes, procedures, elements, schema)
- Constrói grafo direcionado usando NetworkX
- Detecta ciclos (e sugere como quebrá-los)
- Calcula ordem topológica
- Atribui camadas (layer) automaticamente
- Persiste `topological_order` e `layer` de volta no MongoDB

### 2. Tipos de Dependências
| Origem | Dependência | Campo Fonte |
|--------|-------------|-------------|
| Class → Class | Herança | `inherits_from` |
| Class → Class | Uso | `dependencies.uses_classes` |
| Class → Table | Acesso HyperFile | `dependencies.uses_files` |
| Procedure → Procedure | Chamada | `dependencies.calls_procedures` |
| Procedure → Table | Acesso HyperFile | `dependencies.uses_files` |
| Procedure → Class | Instanciação | (a detectar no código) |
| Page → Procedure | Chamada em eventos | `dependencies.uses` |
| Page → Class | Uso de classes | `dependencies.uses` |

### 3. CLI Command
```bash
# Construir grafo e calcular ordem
wxcode analyze-deps ./project-refs/Linkpay_ADM

# Opções
--visualize       # Gera grafo visual (PNG/SVG)
--export-dot      # Exporta para GraphViz DOT
--show-cycles     # Mostra ciclos detectados
--dry-run         # Não persiste no MongoDB
```

### 4. Output Esperado
```
Dependency Graph Analysis
═════════════════════════

Nodes: 751
  - Tables: 45
  - Classes: 14
  - Procedures: 371
  - Pages: 321

Edges: 1,523
  - Class → Class (inheritance): 6
  - Class → Table: 28
  - Procedure → Procedure: 412
  - Procedure → Table: 387
  - Page → Procedure: 690

Cycles Detected: 2
  ⚠ Procedure A → Procedure B → Procedure A
  ⚠ Class X → Class Y → Class X

Layer Assignment:
  Schema (order 0-44): 45 tables
  Domain (order 45-58): 14 classes
  Business (order 59-429): 371 procedures
  UI (order 430-750): 321 pages

✓ Updated topological_order for 751 elements
```

## Scope
- **In scope:**
  - Construção do grafo de dependências
  - Detecção de ciclos
  - Cálculo de ordem topológica
  - Atribuição de camadas
  - Persistência no MongoDB
  - CLI command `analyze-deps`
  - Visualização básica (opcional)

- **Out of scope:**
  - Conversão de código (Fase 4)
  - Análise semântica profunda do código
  - Detecção de dependências em código não parseado

## Dependencies
- **Pré-requisito**: `expand-enrich-dependencies` (extrai procedures locais e dependências de páginas)
- Specs existentes: `class-parsing`, `procedure-parsing`, `schema-parsing`
- Dados já parseados no MongoDB
- NetworkX para algoritmos de grafo

## Risks
1. **Ciclos no grafo**: Ordem topológica não existe para grafos cíclicos
   - Mitigação: Detectar ciclos e sugerir como quebrá-los

2. **Dependências não detectadas**: Código não parseado pode ter dependências ocultas
   - Mitigação: Marcar elementos com dependências incompletas

3. **Performance**: Grafos grandes podem ser lentos
   - Mitigação: Processar em batches, usar algoritmos O(V+E)
