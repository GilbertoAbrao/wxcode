# Design: expand-enrich-dependencies

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      ElementEnricher (expandido)                     │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────────┐ │
│  │  WWHParser   │  │ PDFParser    │  │ DependencyExtractor (NOVO) │ │
│  │  (existente) │  │ (existente)  │  │                            │ │
│  └──────┬───────┘  └──────┬───────┘  └─────────────┬──────────────┘ │
│         │                 │                        │                 │
│         ▼                 ▼                        ▼                 │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    _enrich_element()                         │    │
│  │  1. Parse .wwh/.wdw                                          │    │
│  │  2. Parse PDF                                                │    │
│  │  3. Extract local procedures (NOVO)                          │    │
│  │  4. Extract dependencies from:                               │    │
│  │     - Local procedures (NOVO)                                │    │
│  │     - Control events (NOVO)                                  │    │
│  │     - Page-level code (NOVO)                                 │    │
│  │  5. Save controls                                            │    │
│  │  6. Save local procedures (NOVO)                             │    │
│  │  7. Update Element.dependencies (NOVO)                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │           MongoDB             │
              │  ┌─────────┐  ┌────────────┐  │
              │  │controls │  │procedures  │  │
              │  │         │  │(+is_local) │  │
              │  └─────────┘  └────────────┘  │
              │  ┌─────────────────────────┐  │
              │  │elements.dependencies    │  │
              │  │  uses: [...]            │  │
              │  │  data_files: [...]      │  │
              │  └─────────────────────────┘  │
              └───────────────────────────────┘
```

## Data Flow

```
.wwh/.wdw file
      │
      ▼
┌─────────────────────────────────────────────┐
│              WWHParser                       │
│  ├── page_events[] ──────────────┐          │
│  ├── controls[].events[] ────────┤          │
│  └── local_procedures[] (NOVO) ──┤          │
└──────────────────────────────────┼──────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────┐
│         DependencyExtractor (NOVO)          │
│  Para cada bloco de código:                 │
│  ├── PROCEDURE_CALL_RE → calls_procedures   │
│  ├── HYPERFILE_RE → uses_files              │
│  ├── CLASS_USAGE_RE → uses_classes          │
│  └── API_CALL_RE → external_apis            │
└─────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│              Aggregation                     │
│  Element.dependencies = merge(              │
│    page_event_deps,                         │
│    control_event_deps,                      │
│    local_procedure_deps                     │
│  )                                          │
└─────────────────────────────────────────────┘
```

## New/Modified Models

### Procedure (modificado)
```python
# src/wxcode/models/procedure.py

class Procedure(Document):
    # Campos existentes...

    # NOVO: Distinguir procedures locais de globais
    is_local: bool = Field(
        default=False,
        description="True se é procedure local de página/window"
    )

    # NOVO: Para procedures locais, qual é o escopo
    scope: Optional[str] = Field(
        default=None,
        description="Escopo: 'page', 'window', 'report' ou None para global"
    )
```

### ParsedPage (modificado)
```python
# src/wxcode/parser/wwh_parser.py

@dataclass
class ParsedLocalProcedure:
    """Procedure local extraída da página/window."""
    name: str
    parameters: list[dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    code: str = ""
    code_lines: int = 0
    visibility: str = "private"  # Local procedures são privadas por padrão

@dataclass
class ParsedPage:
    # Campos existentes...

    # NOVO
    local_procedures: list[ParsedLocalProcedure] = field(default_factory=list)
```

### DependencyExtractor (novo)
```python
# src/wxcode/parser/dependency_extractor.py

@dataclass
class ExtractedDependencies:
    """Dependências extraídas de um bloco de código."""
    calls_procedures: list[str] = field(default_factory=list)
    uses_files: list[str] = field(default_factory=list)
    uses_classes: list[str] = field(default_factory=list)
    uses_apis: list[str] = field(default_factory=list)

class DependencyExtractor:
    """
    Extrai dependências de código WLanguage.

    Reutiliza regex do wdg_parser e wdc_parser.
    """

    # Regex para chamadas de procedure
    PROCEDURE_CALL_RE = re.compile(
        r'\b([A-Z][a-zA-Z0-9_]*)\s*\(',
        re.MULTILINE
    )

    # Regex para operações HyperFile
    HYPERFILE_RE = re.compile(
        r'\b(HReadFirst|HReadSeekFirst|HReadNext|HReadLast|'
        r'HAdd|HModify|HDelete|HExecuteQuery|HReset|'
        r'HReadSeek|HFound|HNbRec|HExecuteSQLQuery)\s*\(\s*(\w+)',
        re.IGNORECASE
    )

    # Regex para uso de classes
    CLASS_USAGE_RE = re.compile(
        r'\b(class\w+|_class\w+)\b',
        re.IGNORECASE
    )

    # Regex para APIs REST
    REST_API_RE = re.compile(
        r'\b(RESTSend|HTTPRequest|HTTPGetResult)\s*\(',
        re.IGNORECASE
    )

    # Funções built-in para ignorar
    BUILTIN_FUNCTIONS = {
        'IF', 'THEN', 'ELSE', 'END', 'FOR', 'WHILE', 'SWITCH', 'CASE',
        'RESULT', 'RETURN', 'BREAK', 'CONTINUE', 'LOOP', 'EACH', 'IN',
        'TO', 'Length', 'Left', 'Right', 'Middle', 'Val', 'NoSpace',
        'Upper', 'Lower', 'Contains', 'Serialize', 'Deserialize',
        'DateSys', 'Now', 'DateToString', 'StringToDate', 'GetUUID',
        'Info', 'Trace', 'Error', 'Exception', 'ErrorInfo',
        'Position', 'Replace', 'Complete', 'ExtractString',
        'ArrayAdd', 'ArrayCount', 'ArraySeek', 'ArrayDelete',
        # ... mais funções built-in
    }

    def extract(self, code: str) -> ExtractedDependencies:
        """Extrai dependências de um bloco de código."""
        deps = ExtractedDependencies()

        # Extrai chamadas de procedures
        for match in self.PROCEDURE_CALL_RE.finditer(code):
            proc_name = match.group(1)
            if proc_name not in self.BUILTIN_FUNCTIONS:
                if proc_name not in deps.calls_procedures:
                    deps.calls_procedures.append(proc_name)

        # Extrai operações HyperFile
        for match in self.HYPERFILE_RE.finditer(code):
            file_name = match.group(2)
            if file_name not in deps.uses_files:
                deps.uses_files.append(file_name)

        # Extrai uso de classes
        for match in self.CLASS_USAGE_RE.finditer(code):
            class_name = match.group(1)
            if class_name not in deps.uses_classes:
                deps.uses_classes.append(class_name)

        # Extrai uso de APIs REST
        for match in self.REST_API_RE.finditer(code):
            if "REST" not in deps.uses_apis:
                deps.uses_apis.append("REST")

        return deps

    def merge(self, *deps_list: ExtractedDependencies) -> ExtractedDependencies:
        """Combina múltiplas dependências em uma."""
        merged = ExtractedDependencies()

        for deps in deps_list:
            for proc in deps.calls_procedures:
                if proc not in merged.calls_procedures:
                    merged.calls_procedures.append(proc)
            for file in deps.uses_files:
                if file not in merged.uses_files:
                    merged.uses_files.append(file)
            for cls in deps.uses_classes:
                if cls not in merged.uses_classes:
                    merged.uses_classes.append(cls)
            for api in deps.uses_apis:
                if api not in merged.uses_apis:
                    merged.uses_apis.append(api)

        return merged
```

## ElementEnricher Changes

```python
# src/wxcode/parser/element_enricher.py

class ElementEnricher:

    def __init__(self, ...):
        # ... existente ...
        self.dep_extractor = DependencyExtractor()  # NOVO

    async def _enrich_element(self, element: Element) -> EnrichmentResult:
        # ... código existente até processar wwh_data ...

        # NOVO: Extrai procedures locais
        if wwh_data:
            await self._process_local_procedures(
                element=element,
                wwh_data=wwh_data,
                result=result
            )

        # NOVO: Extrai e agrega dependências
        if wwh_data:
            deps = await self._extract_all_dependencies(
                element=element,
                wwh_data=wwh_data
            )
            element.dependencies = ElementDependencies(
                uses=deps.calls_procedures,
                data_files=deps.uses_files,
                external_apis=deps.uses_apis,
            )

        # ... resto do código existente ...

    async def _process_local_procedures(
        self,
        element: Element,
        wwh_data: ParsedPage,
        result: EnrichmentResult
    ) -> None:
        """Salva procedures locais na collection procedures."""

        for local_proc in wwh_data.local_procedures:
            # Extrai dependências da procedure
            deps = self.dep_extractor.extract(local_proc.code)

            procedure = Procedure(
                project_id=element.project_id,
                element_id=element.id,
                name=local_proc.name,
                parameters=[...],
                return_type=local_proc.return_type,
                code=local_proc.code,
                code_lines=local_proc.code_lines,
                is_local=True,
                scope="page" if element.source_type == ElementType.PAGE else "window",
                dependencies=ProcedureDependencies(
                    calls_procedures=deps.calls_procedures,
                    uses_files=deps.uses_files,
                    uses_apis=deps.uses_apis,
                ),
            )
            await procedure.insert()
            result.local_procedures_created += 1

    async def _extract_all_dependencies(
        self,
        element: Element,
        wwh_data: ParsedPage
    ) -> ExtractedDependencies:
        """Extrai dependências de todas as fontes de código."""

        all_deps = []

        # 1. Eventos da página
        for event in wwh_data.page_events:
            if event.code:
                all_deps.append(self.dep_extractor.extract(event.code))

        # 2. Eventos dos controles
        for control in wwh_data.iter_all_controls():
            for event in control.events:
                if event.code:
                    all_deps.append(self.dep_extractor.extract(event.code))

        # 3. Procedures locais
        for local_proc in wwh_data.local_procedures:
            all_deps.append(self.dep_extractor.extract(local_proc.code))

        # Merge todas as dependências
        return self.dep_extractor.merge(*all_deps)
```

## File Structure

```
src/wxcode/parser/
├── __init__.py                    # Atualizar exports
├── element_enricher.py            # MODIFICAR
├── wwh_parser.py                  # MODIFICAR (extrair local_procedures)
├── dependency_extractor.py        # NOVO
└── ...

src/wxcode/models/
├── procedure.py                   # MODIFICAR (adicionar is_local, scope)
└── ...
```

## Trade-offs

### Onde colocar DependencyExtractor
- **Opção A**: Módulo separado `dependency_extractor.py` (escolhido)
  - Pros: Reutilizável, testável isoladamente
  - Cons: Mais um arquivo

- **Opção B**: Dentro do `element_enricher.py`
  - Pros: Tudo junto
  - Cons: Arquivo fica grande, menos reutilizável

### Reutilizar regex vs duplicar
- **Escolhido**: Criar `DependencyExtractor` com regex consolidados
- Os regex existentes em `wdg_parser` e `wdc_parser` são similares
- Centralizar evita duplicação e facilita manutenção

### Procedures locais: nova collection vs mesma
- **Escolhido**: Mesma collection `procedures` com campo `is_local`
- Pros: Consultas unificadas, mesmo modelo
- Cons: Precisa filtrar por `is_local` quando necessário
