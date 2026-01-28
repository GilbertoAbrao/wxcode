"""
Orquestrador de enriquecimento de elementos.

Combina dados de:
- Arquivo .wwh/.wdw (controles, tipos, hierarquia, eventos)
- PDF de documentação (propriedades visuais)
- Procedures locais extraídas do código da página

E persiste no MongoDB.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from beanie import PydanticObjectId

from wxcode.models import (
    Control,
    ControlEvent,
    ControlProperties,
    ControlTypeDefinition,
    DataBindingInfo,
    Element,
    ElementDependencies,
    ElementType,
    Procedure,
    ProcedureDependencies,
    ProcedureParameter,
    infer_type_name_from_prefix,
    is_container_by_prefix,
)
from wxcode.parser.dependency_extractor import DependencyExtractor
from wxcode.parser.pdf_element_parser import PDFElementParser, ParsedPDFElement
from wxcode.parser.wwh_parser import (
    ParsedControl,
    ParsedLocalProcedure,
    ParsedPage,
    WWHParser,
)


@dataclass
class EnrichmentResult:
    """Resultado do enriquecimento de um elemento."""
    element_name: str
    controls_created: int = 0
    controls_updated: int = 0
    types_discovered: int = 0
    orphan_controls: int = 0
    local_procedures_created: int = 0
    dependencies_extracted: int = 0
    # Estatísticas de matching
    exact_matches: int = 0
    leaf_matches: int = 0
    propagated_matches: int = 0
    ambiguous_matches: int = 0
    # Estatísticas de data binding
    controls_with_binding: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class EnrichmentStats:
    """Estatísticas de enriquecimento de um projeto."""
    elements_processed: int = 0
    elements_skipped: int = 0
    elements_with_errors: int = 0
    total_controls: int = 0
    total_types: int = 0
    total_orphans: int = 0
    total_local_procedures: int = 0
    total_dependencies: int = 0
    # Estatísticas agregadas de matching
    total_exact_matches: int = 0
    total_leaf_matches: int = 0
    total_propagated_matches: int = 0
    total_ambiguous: int = 0
    # Estatísticas agregadas de data binding
    total_controls_with_binding: int = 0
    results: list[EnrichmentResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        """Duração do processamento em segundos."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0


@dataclass
class MatchingContext:
    """
    Contexto de matching entre controles do PDF e do WWH.

    Usado para implementar algoritmo de matching em 3 fases:
    1. Match exato por full_path ou name
    2. Match por leaf name (nome simples, ignorando container)
    3. Propagação de container mapping descoberto
    """

    # Mapa de propriedades do PDF: full_path -> props
    pdf_props: dict[str, dict] = field(default_factory=dict)

    # Índice reverso: leaf_name -> [full_paths no PDF]
    pdf_leaf_index: dict[str, list[str]] = field(default_factory=dict)

    # Container mapping descoberto: wwh_container -> pdf_container
    container_map: dict[str, str] = field(default_factory=dict)

    # Estatísticas de matching
    exact_matches: int = 0
    leaf_matches: int = 0
    propagated_matches: int = 0
    ambiguous: int = 0


logger = logging.getLogger(__name__)


class ElementEnricher:
    """
    Orquestrador que combina dados de:
    - Arquivo .wwh/.wdw (controles, tipos, hierarquia, eventos)
    - PDF de documentação (propriedades visuais)
    """

    # Extensões por tipo de elemento
    ELEMENT_EXTENSIONS = {
        ElementType.PAGE: '.wwh',
        ElementType.PAGE_TEMPLATE: '.wwt',
        ElementType.WINDOW: '.wdw',
        ElementType.REPORT: '.wde',
    }

    def __init__(
        self,
        pdf_docs_dir: Path,
        project_dir: Path,
        screenshots_dir: Optional[Path] = None,
        on_progress: Optional[callable] = None
    ):
        """
        Inicializa o enricher.

        Args:
            pdf_docs_dir: Diretório com PDFs splitados
            project_dir: Diretório do projeto WinDev/WebDev
            screenshots_dir: Diretório para screenshots (opcional)
            on_progress: Callback de progresso (element_name, current, total)
        """
        self.pdf_docs_dir = Path(pdf_docs_dir)
        self.project_dir = Path(project_dir)
        self.screenshots_dir = Path(screenshots_dir) if screenshots_dir else None
        self.on_progress = on_progress

        # Cache de tipos
        self._type_cache: dict[int, ControlTypeDefinition] = {}

        # Extrator de dependências
        self.dep_extractor = DependencyExtractor()

        # Carrega manifest se existir
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> dict[str, Any]:
        """Carrega e deduplica o manifest."""
        manifest_path = self.pdf_docs_dir / "manifest.json"
        if not manifest_path.exists():
            return {"elements": {"pages": [], "reports": [], "windows": []}}

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        # Deduplica elementos (pega primeiro com has_screenshot=true)
        for category in ['pages', 'reports', 'windows']:
            if category not in manifest.get('elements', {}):
                continue

            unique = {}
            for item in manifest['elements'][category]:
                name = item['name']
                if name not in unique or item.get('has_screenshot', False):
                    unique[name] = item

            manifest['elements'][category] = list(unique.values())

        return manifest

    async def enrich_project(self, project_id: PydanticObjectId) -> EnrichmentStats:
        """
        Enriquece todos os elementos de um projeto.

        Args:
            project_id: ID do projeto no MongoDB

        Returns:
            Estatísticas de enriquecimento
        """
        stats = EnrichmentStats(started_at=datetime.utcnow())

        # Busca elementos do projeto (PAGE, WINDOW, REPORT)
        # project_id é um DBRef, então usamos $id para comparar
        # source_type é armazenado como lowercase com underscore (ex: "page", "window", "report")
        elements = await Element.find({
            "project_id.$id": project_id,
            "source_type": {"$in": [
                "page",
                "window",
                "report",
            ]}
        }).to_list()

        total = len(elements)

        for idx, element in enumerate(elements):
            try:
                result = await self._enrich_element(element)
                stats.results.append(result)
                stats.elements_processed += 1
                stats.total_controls += result.controls_created + result.controls_updated
                stats.total_orphans += result.orphan_controls
                stats.total_types += result.types_discovered
                stats.total_local_procedures += result.local_procedures_created
                stats.total_dependencies += result.dependencies_extracted
                # Agrega estatísticas de matching
                stats.total_exact_matches += result.exact_matches
                stats.total_leaf_matches += result.leaf_matches
                stats.total_propagated_matches += result.propagated_matches
                stats.total_ambiguous += result.ambiguous_matches
                # Agrega estatísticas de binding
                stats.total_controls_with_binding += result.controls_with_binding

                if result.errors:
                    stats.elements_with_errors += 1

            except Exception as e:
                stats.elements_skipped += 1
                stats.errors.append(f"{element.source_name}: {str(e)}")

            # Callback de progresso
            if self.on_progress:
                self.on_progress(element.source_name, idx + 1, total)

        stats.completed_at = datetime.utcnow()
        return stats

    async def _enrich_element(self, element: Element) -> EnrichmentResult:
        """
        Enriquece um único elemento.

        Args:
            element: Elemento a enriquecer

        Returns:
            Resultado do enriquecimento
        """
        result = EnrichmentResult(element_name=element.source_name)

        # 1. Encontra e parseia arquivo fonte (.wwh/.wdw)
        source_file = self._find_source_file(element)
        wwh_data: Optional[ParsedPage] = None

        if source_file and source_file.exists():
            try:
                # Lê conteúdo bruto para salvar no elemento
                element.raw_content = source_file.read_text(encoding='utf-8', errors='replace')

                parser = WWHParser(source_file)
                wwh_data = parser.parse()
            except Exception as e:
                result.errors.append(f"Erro ao parsear {source_file.name}: {e}")

        # 2. Encontra e parseia PDF
        pdf_file = self._find_pdf_for_element(element.source_name, element.source_type)
        pdf_data: Optional[ParsedPDFElement] = None

        if pdf_file and pdf_file.exists():
            try:
                pdf_parser = PDFElementParser(pdf_file)
                pdf_data = pdf_parser.parse(self.screenshots_dir)
            except Exception as e:
                result.errors.append(f"Erro ao parsear PDF: {e}")

        # 3. Processa controles
        if wwh_data:
            controls_result = await self._process_controls(
                element=element,
                wwh_data=wwh_data,
                pdf_data=pdf_data
            )
            result.controls_created = controls_result['created']
            result.controls_updated = controls_result['updated']
            result.types_discovered = controls_result['types_discovered']
            result.orphan_controls = controls_result['orphans']
            # Estatísticas de matching
            result.exact_matches = controls_result['exact_matches']
            result.leaf_matches = controls_result['leaf_matches']
            result.propagated_matches = controls_result['propagated_matches']
            result.ambiguous_matches = controls_result['ambiguous']
            result.controls_with_binding = controls_result['controls_with_binding']

        # 4. Processa procedures locais
        if wwh_data and wwh_data.local_procedures:
            procs_created = await self._process_local_procedures(
                element=element,
                local_procedures=wwh_data.local_procedures
            )
            result.local_procedures_created = procs_created

        # 5. Extrai e agrega dependências de todas as fontes
        if wwh_data:
            deps_count = await self._extract_all_dependencies(
                element=element,
                wwh_data=wwh_data
            )
            result.dependencies_extracted = deps_count

        # 6. Atualiza Element
        if pdf_data:
            element.general_properties = pdf_data.general_properties
            element.screenshot_path = pdf_data.screenshot_path

        element.controls_count = result.controls_created + result.controls_updated
        element.updated_at = datetime.utcnow()
        await element.save()

        return result

    def _build_matching_context(
        self,
        pdf_data: Optional[ParsedPDFElement]
    ) -> MatchingContext:
        """
        Constrói contexto de matching entre PDF e WWH.

        Cria índices para busca eficiente por leaf name e prepara
        estruturas para container mapping.

        Args:
            pdf_data: Dados parseados do PDF (pode ser None)

        Returns:
            MatchingContext com índices prontos para uso
        """
        ctx = MatchingContext()

        if not pdf_data or not pdf_data.control_properties:
            logger.warning("No PDF data available - all controls will be orphans")
            return ctx

        ctx.pdf_props = pdf_data.control_properties

        # Constrói índice reverso: leaf_name -> [full_paths]
        for full_path in ctx.pdf_props.keys():
            # Extrai leaf name (última parte do path)
            leaf = full_path.rsplit('.', 1)[-1]
            if leaf not in ctx.pdf_leaf_index:
                ctx.pdf_leaf_index[leaf] = []
            ctx.pdf_leaf_index[leaf].append(full_path)

        return ctx

    def _match_control(
        self,
        wwh_ctrl: ParsedControl,
        ctx: MatchingContext
    ) -> tuple[Optional[dict], bool]:
        """
        Tenta fazer match de um controle WWH com o PDF usando 3 fases.

        Fase 1: Match exato por full_path ou name
        Fase 2: Match por leaf name (único candidato)
        Fase 3: Propagação de container mapping descoberto

        Args:
            wwh_ctrl: Controle parseado do WWH
            ctx: Contexto de matching com índices

        Returns:
            Tupla (propriedades_pdf, is_orphan)
        """
        # Se não há dados do PDF, todos são órfãos
        if not ctx.pdf_props:
            return None, True  # Warning será logado em _build_matching_context

        # Fase 1: Match exato por full_path
        props = ctx.pdf_props.get(wwh_ctrl.full_path)
        if props:
            ctx.exact_matches += 1
            return props, False

        # Fase 1b: Match exato por name simples
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

            # Registra container mapping se ambos têm pai
            if '.' in wwh_ctrl.full_path and '.' in pdf_path:
                wwh_parent = wwh_ctrl.full_path.rsplit('.', 1)[0]
                pdf_parent = pdf_path.rsplit('.', 1)[0]
                if wwh_parent != pdf_parent:
                    ctx.container_map[wwh_parent] = pdf_parent
                    logger.debug(
                        "Container mapped: %s → %s (via %s)",
                        wwh_parent, pdf_parent, leaf
                    )

            return props, False

        if len(candidates) > 1:
            ctx.ambiguous += 1
            logger.warning(
                "Ambiguous leaf '%s': %d candidates in PDF: %s",
                leaf, len(candidates), candidates[:5]  # Limita a 5 para não poluir
            )

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

        # Órfão: não encontrou match
        return None, True

    async def _process_controls(
        self,
        element: Element,
        wwh_data: ParsedPage,
        pdf_data: Optional[ParsedPDFElement]
    ) -> dict[str, int]:
        """
        Processa controles: combina .wwh + PDF e salva no MongoDB.

        Args:
            element: Elemento pai
            wwh_data: Dados parseados do .wwh
            pdf_data: Dados parseados do PDF

        Returns:
            Contadores de operações
        """
        result = {
            'created': 0,
            'updated': 0,
            'types_discovered': 0,
            'orphans': 0,
            'exact_matches': 0,
            'leaf_matches': 0,
            'propagated_matches': 0,
            'ambiguous': 0,
            'controls_with_binding': 0,
        }

        # Constrói contexto de matching com índices
        # O PDF do elemento pai contém todos os controles, incluindo os de POPUPs
        # com paths completos como "POPUP_ITEM.EDT_NOME"
        match_ctx = self._build_matching_context(pdf_data)

        # Primeira passada: cria/atualiza controles sem hierarquia
        control_map: dict[str, Control] = {}  # full_path -> Control

        for parsed_ctrl in wwh_data.iter_all_controls():
            # Obtém ou cria tipo
            type_def, is_new_type = await self._get_or_create_type(
                parsed_ctrl.type_code,
                parsed_ctrl.name,
                element.source_name
            )
            if is_new_type:
                result['types_discovered'] += 1

            # Busca propriedades do PDF usando algoritmo de 3 fases
            # Controles dentro de POPUPs/ZONEs usam o mesmo contexto
            # pois o PDF lista com path completo (ex: POPUP_ITEM.EDT_NOME)
            ctrl_pdf_props, is_orphan = self._match_control(parsed_ctrl, match_ctx)

            if is_orphan:
                result['orphans'] += 1

            # Monta propriedades
            properties = None
            if ctrl_pdf_props:
                # Plane pode ser int ou string, converte para string
                plane_val = ctrl_pdf_props.get('Plane(s) containing the control')
                if plane_val is not None:
                    plane_val = str(plane_val)

                properties = ControlProperties(
                    height=ctrl_pdf_props.get('Height'),
                    width=ctrl_pdf_props.get('Width'),
                    x_position=ctrl_pdf_props.get('X position'),
                    y_position=ctrl_pdf_props.get('Y position'),
                    visible=ctrl_pdf_props.get('Visible', True),
                    enabled=ctrl_pdf_props.get('Enabled', True),
                    input_type=ctrl_pdf_props.get('Input type'),
                    style=ctrl_pdf_props.get('Style'),
                    tooltip=ctrl_pdf_props.get('Tooltip'),
                    html_class=ctrl_pdf_props.get('HTMLClass'),
                    anchor=ctrl_pdf_props.get('Anchor'),
                    plane=plane_val,
                    tab_order=ctrl_pdf_props.get('Tab order'),
                    caption=ctrl_pdf_props.get('Caption'),
                    hint_text=ctrl_pdf_props.get('Hint text if empty'),
                    required=ctrl_pdf_props.get('Required input', False),
                )

            # Extrai data binding (se disponível no PDF)
            data_binding: Optional[DataBindingInfo] = None
            is_bound = False
            if ctrl_pdf_props and '_data_binding' in ctrl_pdf_props:
                data_binding = ctrl_pdf_props['_data_binding']
                is_bound = True
                result['controls_with_binding'] += 1

            # Monta eventos
            events = [
                ControlEvent(
                    type_code=e.type_code,
                    event_name=None,  # Será preenchido depois com curadoria
                    code=e.code,
                    role=e.role,
                    enabled=e.enabled
                )
                for e in parsed_ctrl.events
            ]

            # Verifica se já existe
            existing = await Control.find_one(
                Control.element_id == element.id,
                Control.name == parsed_ctrl.name
            )

            if existing:
                # Atualiza
                existing.type_code = parsed_ctrl.type_code
                existing.type_definition_id = type_def.id if type_def else None
                existing.full_path = parsed_ctrl.full_path
                existing.depth = parsed_ctrl.depth
                existing.properties = properties
                existing.events = events
                existing.raw_properties = ctrl_pdf_props or {}
                existing.code_blocks = parsed_ctrl.code_blocks
                existing.windev_internal_properties = parsed_ctrl.internal_properties
                existing.is_orphan = is_orphan
                existing.is_container = parsed_ctrl.is_container or is_container_by_prefix(parsed_ctrl.name)
                existing.has_code = parsed_ctrl.has_code
                existing.data_binding = data_binding
                existing.is_bound = is_bound
                existing.updated_at = datetime.utcnow()
                await existing.save()
                control_map[parsed_ctrl.full_path] = existing
                result['updated'] += 1
            else:
                # Cria novo
                control = Control(
                    element_id=element.id,
                    project_id=element.project_id.ref.id if hasattr(element.project_id, 'ref') else element.project_id,
                    type_code=parsed_ctrl.type_code,
                    type_definition_id=type_def.id if type_def else None,
                    name=parsed_ctrl.name,
                    full_path=parsed_ctrl.full_path,
                    depth=parsed_ctrl.depth,
                    properties=properties,
                    events=events,
                    raw_properties=ctrl_pdf_props or {},
                    code_blocks=parsed_ctrl.code_blocks,
                    windev_internal_properties=parsed_ctrl.internal_properties,
                    is_orphan=is_orphan,
                    is_container=parsed_ctrl.is_container or is_container_by_prefix(parsed_ctrl.name),
                    has_code=parsed_ctrl.has_code,
                    data_binding=data_binding,
                    is_bound=is_bound,
                )
                await control.insert()
                control_map[parsed_ctrl.full_path] = control
                result['created'] += 1

        # Segunda passada: atualiza hierarquia
        for parsed_ctrl in wwh_data.iter_all_controls():
            control = control_map.get(parsed_ctrl.full_path)
            if not control:
                continue

            # Parent
            if parsed_ctrl.parent_name and parsed_ctrl.parent_name in control_map:
                parent = control_map[parsed_ctrl.parent_name]
                control.parent_control_id = parent.id
                await control.save()

            # Children
            children_ids = []
            for child in parsed_ctrl.children:
                child_ctrl = control_map.get(child.full_path)
                if child_ctrl:
                    children_ids.append(child_ctrl.id)

            if children_ids:
                control.children_ids = children_ids
                await control.save()

        # Copia estatísticas de matching para o resultado
        result['exact_matches'] = match_ctx.exact_matches
        result['leaf_matches'] = match_ctx.leaf_matches
        result['propagated_matches'] = match_ctx.propagated_matches
        result['ambiguous'] = match_ctx.ambiguous

        # Log de estatísticas de matching
        total_matched = (
            result['exact_matches'] +
            result['leaf_matches'] +
            result['propagated_matches']
        )
        logger.info(
            "Matching: %d exact, %d by-leaf, %d propagated, %d ambiguous, %d orphans",
            result['exact_matches'],
            result['leaf_matches'],
            result['propagated_matches'],
            result['ambiguous'],
            result['orphans']
        )

        # Log de estatísticas de binding
        total_controls = result['created'] + result['updated']
        if total_controls > 0:
            binding_pct = (result['controls_with_binding'] / total_controls) * 100
            logger.info(
                "Binding: %d/%d controles com binding (%.1f%%)",
                result['controls_with_binding'],
                total_controls,
                binding_pct
            )

        return result

    async def _process_local_procedures(
        self,
        element: Element,
        local_procedures: list[ParsedLocalProcedure]
    ) -> int:
        """
        Processa procedures locais e salva no MongoDB.

        Args:
            element: Elemento pai (página/window)
            local_procedures: Lista de procedures locais parseadas

        Returns:
            Número de procedures criadas
        """
        created = 0

        # Determina scope baseado no tipo do elemento
        scope = None
        if element.source_type == ElementType.PAGE:
            scope = "page"
        elif element.source_type == ElementType.WINDOW:
            scope = "window"
        elif element.source_type == ElementType.REPORT:
            scope = "report"

        for parsed_proc in local_procedures:
            # Verifica se já existe
            existing = await Procedure.find_one(
                Procedure.element_id == element.id,
                Procedure.name == parsed_proc.name
            )

            if existing:
                # Atualiza procedure existente
                existing.parameters = [
                    ProcedureParameter(
                        name=p.name,
                        type=p.type,
                        is_local=p.is_local,
                        default_value=p.default_value
                    )
                    for p in parsed_proc.parameters
                ]
                existing.return_type = parsed_proc.return_type
                existing.code = parsed_proc.code
                existing.code_lines = parsed_proc.code_lines
                existing.has_documentation = parsed_proc.has_documentation
                existing.is_internal = parsed_proc.is_internal
                existing.has_error_handling = parsed_proc.has_error_handling
                existing.is_local = True
                existing.scope = scope

                # Extrai dependências
                deps = self.dep_extractor.extract(parsed_proc.code)
                existing.dependencies = ProcedureDependencies(
                    calls_procedures=deps.calls_procedures,
                    uses_files=deps.uses_files,
                    uses_apis=deps.uses_apis,
                )

                existing.updated_at = datetime.utcnow()
                await existing.save()
            else:
                # Extrai dependências
                deps = self.dep_extractor.extract(parsed_proc.code)

                # Cria nova procedure
                procedure = Procedure(
                    element_id=element.id,
                    project_id=element.project_id.ref.id if hasattr(element.project_id, 'ref') else element.project_id,
                    name=parsed_proc.name,
                    parameters=[
                        ProcedureParameter(
                            name=p.name,
                            type=p.type,
                            is_local=p.is_local,
                            default_value=p.default_value
                        )
                        for p in parsed_proc.parameters
                    ],
                    return_type=parsed_proc.return_type,
                    code=parsed_proc.code,
                    code_lines=parsed_proc.code_lines,
                    dependencies=ProcedureDependencies(
                        calls_procedures=deps.calls_procedures,
                        uses_files=deps.uses_files,
                        uses_apis=deps.uses_apis,
                    ),
                    has_documentation=parsed_proc.has_documentation,
                    is_internal=parsed_proc.is_internal,
                    has_error_handling=parsed_proc.has_error_handling,
                    is_local=True,
                    scope=scope,
                )
                await procedure.insert()
                created += 1

        return created

    async def _extract_all_dependencies(
        self,
        element: Element,
        wwh_data: ParsedPage
    ) -> int:
        """
        Extrai e agrega dependências de todas as fontes do elemento.

        Fontes:
        - Código da página (page_code)
        - Eventos de controles
        - Procedures locais

        Args:
            element: Elemento a atualizar
            wwh_data: Dados parseados do .wwh

        Returns:
            Total de dependências extraídas
        """
        all_code_blocks = []

        # 1. Código da página
        if wwh_data.page_code:
            all_code_blocks.append(wwh_data.page_code)

        # 2. Código dos eventos de controles
        for ctrl in wwh_data.iter_all_controls():
            for event in ctrl.events:
                if event.code:
                    all_code_blocks.append(event.code)

        # 3. Código das procedures locais
        for proc in wwh_data.local_procedures:
            if proc.code:
                all_code_blocks.append(proc.code)

        # Extrai e combina dependências
        deps = self.dep_extractor.extract_and_merge(*all_code_blocks)

        # Atualiza Element.dependencies
        if not element.dependencies:
            element.dependencies = ElementDependencies()

        # Merge com dependências existentes (não sobrescreve)
        for proc in deps.calls_procedures:
            if proc not in element.dependencies.uses:
                element.dependencies.uses.append(proc)

        for file in deps.uses_files:
            if file not in element.dependencies.data_files:
                element.dependencies.data_files.append(file)

        for api in deps.uses_apis:
            if api not in element.dependencies.external_apis:
                element.dependencies.external_apis.append(api)

        for cls in deps.uses_classes:
            if cls not in element.dependencies.uses:
                element.dependencies.uses.append(cls)

        # Salva elemento (será salvo no método pai, mas atualizamos dependencies aqui)
        return deps.total_count

    async def _get_or_create_type(
        self,
        type_code: int,
        control_name: str,
        element_name: str
    ) -> tuple[ControlTypeDefinition, bool]:
        """
        Obtém ou cria definição de tipo.

        Args:
            type_code: Código numérico do tipo
            control_name: Nome do controle (para inferir nome)
            element_name: Nome do elemento (para first_seen_in)

        Returns:
            Tupla (ControlTypeDefinition, is_new) onde is_new indica se o tipo foi criado
        """
        # Cache
        if type_code in self._type_cache:
            type_def = self._type_cache[type_code]
            type_def.increment_occurrences()
            type_def.add_example(control_name)
            await type_def.save()
            return type_def, False

        # Busca no banco
        type_def = await ControlTypeDefinition.find_one(
            ControlTypeDefinition.type_code == type_code
        )

        if type_def:
            type_def.increment_occurrences()
            type_def.add_example(control_name)
            await type_def.save()
            self._type_cache[type_code] = type_def
            return type_def, False

        # Cria novo
        inferred_name = infer_type_name_from_prefix(control_name)
        is_container = is_container_by_prefix(control_name)

        type_def = ControlTypeDefinition(
            type_code=type_code,
            inferred_name=inferred_name,
            is_container=is_container,
            first_seen_in=element_name,
            occurrences=1,
            example_names=[control_name]
        )
        await type_def.insert()
        self._type_cache[type_code] = type_def
        return type_def, True

    def _find_source_file(self, element: Element) -> Optional[Path]:
        """
        Encontra arquivo fonte do elemento.

        Args:
            element: Elemento

        Returns:
            Path do arquivo ou None
        """
        ext = self.ELEMENT_EXTENSIONS.get(element.source_type)
        if not ext:
            return None

        # Tenta pelo source_file
        if element.source_file:
            # Remove .\ do início se existir
            source_file = element.source_file.lstrip('.\\').lstrip('./')
            path = self.project_dir / source_file
            if path.exists():
                return path

        # Tenta pelo nome
        path = self.project_dir / f"{element.source_name}{ext}"
        if path.exists():
            return path

        return None

    def _find_pdf_for_element(
        self,
        element_name: str,
        element_type: ElementType
    ) -> Optional[Path]:
        """
        Encontra PDF do elemento no manifest.

        Args:
            element_name: Nome do elemento
            element_type: Tipo do elemento

        Returns:
            Path do PDF ou None
        """
        # Determina categoria
        category = 'pages'
        if element_type == ElementType.REPORT:
            category = 'reports'
        elif element_type == ElementType.WINDOW:
            category = 'windows'

        # Busca no manifest
        for item in self.manifest.get('elements', {}).get(category, []):
            if item.get('name') == element_name:
                pdf_path = self.pdf_docs_dir / item['pdf_file']
                if pdf_path.exists():
                    return pdf_path

        # Fallback: busca direta
        pdf_path = self.pdf_docs_dir / category / f"{element_name}.pdf"
        if pdf_path.exists():
            return pdf_path

        return None


async def enrich_project_elements(
    project_id: PydanticObjectId,
    pdf_docs_dir: Path,
    project_dir: Path,
    screenshots_dir: Optional[Path] = None,
    on_progress: Optional[callable] = None
) -> EnrichmentStats:
    """
    Função de conveniência para enriquecer elementos de um projeto.

    Args:
        project_id: ID do projeto
        pdf_docs_dir: Diretório com PDFs
        project_dir: Diretório do projeto WinDev
        screenshots_dir: Diretório para screenshots
        on_progress: Callback de progresso

    Returns:
        Estatísticas de enriquecimento
    """
    enricher = ElementEnricher(
        pdf_docs_dir=pdf_docs_dir,
        project_dir=project_dir,
        screenshots_dir=screenshots_dir,
        on_progress=on_progress
    )
    return await enricher.enrich_project(project_id)
