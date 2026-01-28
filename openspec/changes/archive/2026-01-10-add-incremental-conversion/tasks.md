# Tasks: add-incremental-conversion

## Task 1: Criar SpecContextLoader

**File:** `src/wxcode/llm_converter/spec_context_loader.py`

**Steps:**
1. Criar classe `SpecContextLoader` com `__init__(specs_dir: Path)`
2. Implementar método `load_dependency_specs(element: Element) -> tuple[list, list]`
3. Para cada item em `element.dependencies.uses`, buscar spec arquivada
4. Retornar conteúdo das specs encontradas e lista de missing

**Acceptance Criteria:**
- [x] Carrega specs de `openspec/specs/{element}-spec/spec.md`
- [x] Retorna lista vazia se spec não existe
- [x] Formata specs como contexto para LLM

---

## Task 2: Criar ProposalGenerator

**File:** `src/wxcode/llm_converter/proposal_generator.py`

**Steps:**
1. Criar classe `ProposalGenerator` com `__init__(provider, output_dir)`
2. Implementar método `async generate(element, dep_specs_context) -> ProposalOutput`
3. Implementar método `async generate_and_save(element, context) -> tuple[ProposalOutput, Path]`
4. Usar prompt específico para gerar proposal.md, tasks.md, spec.md

**Acceptance Criteria:**
- [x] Gera proposal.md com summary, problem, solution
- [x] Gera tasks.md com passos de implementação
- [x] Gera spec.md com `## ADDED Requirements` e scenarios
- [x] Usa specs das dependências como contexto

---

## Task 3: Criar ConversionTracker

**File:** `src/wxcode/llm_converter/conversion_tracker.py`

**Steps:**
1. Criar classe `ConversionTracker` com `__init__(db)`
2. Implementar `async get_next_pending(project_name) -> Element | None`
3. Implementar `async mark_status(element_id, status: str)`
4. Status: "pending", "proposal_generated", "converted", "archived"

**Acceptance Criteria:**
- [x] Busca próximo elemento por `topological_order` com status "pending"
- [x] Prioriza elementos COM ordem topológica antes dos SEM
- [x] Atualiza campo `conversion.status` no MongoDB
- [x] Usa `project_id.$id` para queries com DBRef

---

## Task 4: Criar dataclasses de suporte

**File:** `src/wxcode/llm_converter/models.py`

**Steps:**
1. Adicionar dataclass `ProposalOutput` com campos: element_id, element_name, proposal_md, tasks_md, spec_md, design_md, missing_deps
2. Adicionar dataclass `MappingDecision` e `ConversionSpec`

**Acceptance Criteria:**
- [x] `ProposalOutput` com type hints completos
- [x] `ConversionSpec` documenta decisões de mapeamento

---

## Task 5: Adicionar prompt para geração de proposals

**File:** `src/wxcode/llm_converter/providers/prompts.py`

**Steps:**
1. Adicionar `PROPOSAL_GENERATION_PROMPT`
2. Incluir instruções para formato OpenSpec com `## ADDED Requirements`
3. Incluir template de spec.md com requirements/scenarios
4. Adicionar exemplo completo de spec válida

**Acceptance Criteria:**
- [x] Prompt instrui formato correto com `## ADDED Requirements`
- [x] Cada requirement tem frase com MUST/SHOULD
- [x] Inclui exemplos de spec.md válida
- [x] Orienta uso de specs das dependências

---

## Task 6: Adicionar comando convert-next ao CLI

**File:** `src/wxcode/cli.py`

**Steps:**
1. Adicionar comando `convert-next` com argumento `project_name`
2. Opção `--output` com default `output/openspec/changes`
3. Opção `--auto` para modo automático (sem pausa para revisão)
4. Opção `--dry-run` para apenas mostrar próximo elemento
5. Integrar ConversionTracker, SpecContextLoader, ProposalGenerator

**Acceptance Criteria:**
- [x] `wxcode convert-next Linkpay_ADM` gera proposal
- [x] `--auto` executa validate após gerar
- [x] `--dry-run` mostra próximo sem gerar
- [x] Proposals geradas em `output/openspec/changes/`

---

## Task 7: Exportar novos módulos

**File:** `src/wxcode/llm_converter/__init__.py`

**Steps:**
1. Adicionar exports para SpecContextLoader, ProposalGenerator, ConversionTracker
2. Adicionar exports para ProposalOutput, ConversionSpec, MappingDecision
3. Atualizar `__all__`

**Acceptance Criteria:**
- [x] Todos os novos módulos exportados
- [x] Imports funcionam corretamente

---

## Task 8: Atualizar README.md

**File:** `README.md`

**Steps:**
1. Adicionar seção "Conversão Incremental (convert-next)"
2. Documentar fluxo completo com comandos
3. Atualizar tabela de status

**Acceptance Criteria:**
- [x] Seção com fluxo passo a passo
- [x] Estrutura de diretórios documentada
- [x] Status 4.7 adicionado na tabela
