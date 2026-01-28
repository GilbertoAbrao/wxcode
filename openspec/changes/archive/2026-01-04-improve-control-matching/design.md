# Design: Improve Control Matching

## Algoritmo Proposto

### Estratégia de Matching em 3 Fases

```
FASE 1: Match Exato (atual)
─────────────────────────────────────
Para cada controle do .wwh:
  1. Tenta match por full_path exato
  2. Se não, tenta match por name exato
  3. Se encontrou → matched
  4. Se não → vai para Fase 2

FASE 2: Match por Leaf Name
─────────────────────────────────────
Para controles não-matched:
  1. Extrai leaf_name (última parte do path)
  2. Busca no PDF controles com mesmo leaf_name
  3. Se único match → matched + registra container mapping
  4. Se múltiplos → marca como ambíguo, continua órfão

FASE 3: Container Mapping Propagation
─────────────────────────────────────
Com base nos matches da Fase 2:
  1. Detecta padrões: ZONE_NoName2 → POPUP_ITEM
  2. Reprocessa órfãos cujo pai foi mapeado
  3. Atualiza full_path no PDF usando mapeamento
```

### Estrutura de Dados

```python
@dataclass
class MatchingContext:
    """Contexto de matching entre PDF e WWH."""

    # Mapa de propriedades do PDF: full_path -> props
    pdf_props: dict[str, dict]

    # Índice reverso: leaf_name -> [full_paths no PDF]
    pdf_leaf_index: dict[str, list[str]]

    # Container mapping descoberto: wwh_container -> pdf_container
    container_map: dict[str, str]

    # Estatísticas
    exact_matches: int = 0
    leaf_matches: int = 0
    propagated_matches: int = 0
    ambiguous: int = 0
```

### Implementação

**Arquivo:** `src/wxcode/parser/element_enricher.py`

**Mudanças:**
1. Novo método `_build_matching_context()` - constrói índices
2. Novo método `_match_control()` - implementa 3 fases
3. Atualiza `_process_controls()` - usa novo algoritmo

### Pseudocódigo

```python
def _build_matching_context(self, pdf_data: ParsedPDFElement) -> MatchingContext:
    ctx = MatchingContext()
    ctx.pdf_props = pdf_data.control_properties

    # Constrói índice por leaf name
    for full_path in ctx.pdf_props.keys():
        leaf = full_path.rsplit('.', 1)[-1]  # Última parte
        ctx.pdf_leaf_index.setdefault(leaf, []).append(full_path)

    return ctx

def _match_control(
    self,
    wwh_ctrl: ParsedControl,
    ctx: MatchingContext
) -> tuple[dict | None, bool]:  # (props, is_orphan)

    # Fase 1: Match exato
    props = ctx.pdf_props.get(wwh_ctrl.full_path)
    if props:
        ctx.exact_matches += 1
        return props, False

    props = ctx.pdf_props.get(wwh_ctrl.name)
    if props:
        ctx.exact_matches += 1
        return props, False

    # Fase 2: Match por leaf name
    leaf = wwh_ctrl.name  # Nome simples já é o leaf
    candidates = ctx.pdf_leaf_index.get(leaf, [])

    if len(candidates) == 1:
        pdf_path = candidates[0]
        props = ctx.pdf_props[pdf_path]
        ctx.leaf_matches += 1

        # Registra container mapping se aplicável
        if '.' in wwh_ctrl.full_path and '.' in pdf_path:
            wwh_parent = wwh_ctrl.full_path.rsplit('.', 1)[0]
            pdf_parent = pdf_path.rsplit('.', 1)[0]
            if wwh_parent != pdf_parent:
                ctx.container_map[wwh_parent] = pdf_parent

        return props, False

    if len(candidates) > 1:
        ctx.ambiguous += 1

    # Fase 3: Tenta container mapping propagado
    if '.' in wwh_ctrl.full_path:
        wwh_parent = wwh_ctrl.full_path.rsplit('.', 1)[0]
        if wwh_parent in ctx.container_map:
            pdf_parent = ctx.container_map[wwh_parent]
            mapped_path = f"{pdf_parent}.{leaf}"
            props = ctx.pdf_props.get(mapped_path)
            if props:
                ctx.propagated_matches += 1
                return props, False

    return None, True  # Órfão
```

## Trade-offs

### Opção A: Match por Leaf (Escolhida)
- **Prós:** Simples, resolve maioria dos casos
- **Contras:** Pode ter falso positivo se mesmo nome em contextos diferentes

### Opção B: Match por Estrutura de Filhos
- **Prós:** Mais preciso para containers
- **Contras:** Complexo, requer análise de grafo

### Opção C: Match por Posição/Dimensões
- **Prós:** Muito preciso
- **Contras:** Nem sempre disponível, muito complexo

## Observabilidade

Adicionar logging detalhado:
```
[INFO] Matching: 85 exact, 32 by-leaf, 12 propagated, 5 ambiguous, 3 orphans
[WARN] Ambiguous leaf 'EDT_NOME': 3 candidates in PDF
[DEBUG] Container mapped: POPUP_ITEM → ZONE_NoName2
```
