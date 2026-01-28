"""
Mapeador de elementos de projeto com streaming.

Processa arquivos .wwp/.wdp grandes (100k+ linhas) de forma eficiente,
extraindo todos os elementos e inserindo no MongoDB em batches.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from pathlib import Path
from typing import Optional

from wxcode.models import (
    Project,
    ProjectStatus,
    ProjectConfiguration,
    Element,
    ElementType,
    ElementLayer,
    ElementDependencies,
    ElementConversion,
)
from .line_reader import read_lines, LineContext, count_lines


logger = logging.getLogger(__name__)


class ParserState(Enum):
    """Estados do parser durante streaming."""
    INITIAL = "initial"
    IN_PROJECT = "in_project"
    IN_CONFIGURATIONS = "in_configurations"
    IN_CONFIG_ITEM = "in_config_item"
    IN_ELEMENTS = "in_elements"
    IN_ELEMENT_ITEM = "in_element_item"
    IN_ELEMENT_CONFIGS = "in_element_configs"  # Configurações aninhadas no elemento
    IN_CODE_ELEMENTS = "in_code_elements"  # Seção code_elements do projeto
    DONE = "done"


# Mapeamento de tipo numérico WinDev para ElementType
WINDEV_TYPE_MAP: dict[int, ElementType] = {
    65538: ElementType.PAGE,
    65541: ElementType.PAGE_TEMPLATE,
    65539: ElementType.BROWSER_PROCEDURE,
    7: ElementType.PROCEDURE_GROUP,
    4: ElementType.CLASS,
    5: ElementType.QUERY,
    22: ElementType.WEBSERVICE,
}

# Mapeamento de extensão para ElementType (fallback)
EXTENSION_TYPE_MAP: dict[str, ElementType] = {
    ".wwh": ElementType.PAGE,
    ".wwt": ElementType.PAGE_TEMPLATE,
    ".wwn": ElementType.BROWSER_PROCEDURE,
    ".wdg": ElementType.PROCEDURE_GROUP,
    ".wdc": ElementType.CLASS,
    ".wdr": ElementType.QUERY,
    ".wde": ElementType.REPORT,
    ".wdrest": ElementType.REST_API,
    ".wdsdl": ElementType.WEBSERVICE,
    ".wdw": ElementType.WINDOW,
}

# Mapeamento de ElementType para ElementLayer
TYPE_LAYER_MAP: dict[ElementType, ElementLayer] = {
    ElementType.QUERY: ElementLayer.SCHEMA,
    ElementType.CLASS: ElementLayer.DOMAIN,
    ElementType.PROCEDURE_GROUP: ElementLayer.BUSINESS,
    ElementType.REST_API: ElementLayer.API,
    ElementType.WEBSERVICE: ElementLayer.API,
    ElementType.PAGE: ElementLayer.UI,
    ElementType.PAGE_TEMPLATE: ElementLayer.UI,
    ElementType.BROWSER_PROCEDURE: ElementLayer.UI,
    ElementType.WINDOW: ElementLayer.UI,
    ElementType.REPORT: ElementLayer.UI,
}


@dataclass
class MappingStats:
    """Estatísticas do mapeamento."""
    total_lines: int = 0
    lines_processed: int = 0
    elements_found: int = 0
    elements_saved: int = 0
    configurations_found: int = 0
    errors: list = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        """Retorna a duração do processamento em segundos."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

    @property
    def progress_percent(self) -> float:
        """Retorna o progresso em porcentagem."""
        if self.total_lines == 0:
            return 0
        return (self.lines_processed / self.total_lines) * 100


@dataclass
class ElementInfo:
    """Informações de um elemento extraído."""
    name: str = ""
    identifier: str = ""
    windev_type: Optional[int] = None
    physical_name: str = ""
    excluded_from: list[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Verifica se tem informações mínimas."""
        return bool(self.name and self.physical_name)


class ProjectElementMapper:
    """
    Mapeia elementos de projetos WinDev/WebDev para MongoDB.

    Usa streaming para processar arquivos grandes eficientemente.
    """

    # Tamanho do batch para inserção no MongoDB
    BATCH_SIZE = 100

    def __init__(
        self,
        project_file: Path,
        on_progress: Optional[callable] = None,
        workspace_id: Optional[str] = None,
        workspace_path: Optional[str] = None,
    ):
        """
        Inicializa o mapper.

        Args:
            project_file: Caminho para arquivo .wwp ou .wdp
            on_progress: Callback de progresso (lines_done, total_lines, elements_found)
            workspace_id: ID do workspace (8 hex chars) para associar ao projeto
            workspace_path: Caminho do diretorio do workspace
        """
        self.project_file = Path(project_file)
        self.project_dir = self.project_file.parent
        self.on_progress = on_progress
        self.workspace_id = workspace_id
        self.workspace_path = workspace_path

        if not self.project_file.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {project_file}")

        ext = self.project_file.suffix.lower()
        if ext not in [".wwp", ".wdp", ".wpp"]:
            raise ValueError(f"Extensão não suportada: {ext}. Use .wwp, .wdp ou .wpp")

        self.stats = MappingStats()
        self._state = ParserState.INITIAL
        self._project_data: dict = {}
        self._current_config: dict = {}
        self._current_element: ElementInfo = ElementInfo()
        self._configurations: list[ProjectConfiguration] = []
        self._element_batch: list[Element] = []
        self._section_indent: int = 0
        self._element_indent: int = -1  # Indent dos elementos (primeiro - encontrado)
        # Controle de configurações aninhadas no elemento
        self._element_config_indent: int = -1  # Indent da seção configurations do elemento
        self._current_element_config_id: str = ""  # ID da configuração atual do elemento
        self._in_element_config_item: bool = False  # Se está dentro de um item da lista
        # Controle de seção code_elements
        self._code_elements_data: dict = {}
        self._code_elements_indent: int = -1
        self._in_code_block: bool = False
        self._code_block_content: list[str] = []

    async def map(self) -> tuple[Project, MappingStats]:
        """
        Executa o mapeamento completo.

        Returns:
            Tupla (Project salvo, estatísticas)
        """
        self.stats.start_time = datetime.now()

        # Conta linhas para progresso
        self.stats.total_lines = await count_lines(self.project_file)

        # Primeira passada: extrai metadados do projeto
        await self._extract_project_metadata()

        # Cria e salva projeto no MongoDB
        project = await self._create_project()
        await project.insert()

        # Segunda passada: extrai e salva elementos em streaming
        await self._stream_elements(project)

        # Salva último elemento pendente
        if self._current_element.is_valid():
            await self._add_element_to_batch(project)

        # Salva último batch
        if self._element_batch:
            await self._save_batch(project)

        # Extrai e salva Project Code se existir
        project_code_element = self._extract_project_code_element(project)
        if project_code_element:
            await project_code_element.insert()
            self.stats.elements_saved += 1
            logger.info(f"Project Code element criado: {project_code_element.source_name}")

        # Atualiza projeto com contagem final
        project.total_elements = self.stats.elements_saved
        project.elements_by_type = await self._count_elements_by_type(project)
        project.status = ProjectStatus.IMPORTED
        await project.save()

        self.stats.end_time = datetime.now()

        return project, self.stats

    async def _extract_project_metadata(self):
        """Extrai metadados básicos do projeto (primeira passada rápida)."""
        self._state = ParserState.INITIAL
        in_info_section = False

        async for ctx in read_lines(self.project_file):
            # Processa apenas início do arquivo
            if ctx.line_number > 500:  # Metadados estão no início
                break

            # Detecta seção "info :" (alguns projetos usam essa seção)
            if ctx.stripped == "info :":
                in_info_section = True
                continue

            # Detecta seção "project :"
            if ctx.stripped == "project :":
                in_info_section = False
                self._state = ParserState.IN_PROJECT
                continue

            # Extrai dados da seção "info :" ou "project :"
            if (in_info_section or self._state == ParserState.IN_PROJECT) and ctx.is_key_value:
                key, value = ctx.parse_key_value()

                if key == "name" and not self._project_data.get("name"):
                    self._project_data["name"] = value
                elif key == "major_version":
                    self._project_data["major_version"] = int(value) if value else 28
                elif key == "minor_version":
                    self._project_data["minor_version"] = int(value) if value else 0
                elif key == "type":
                    self._project_data["type"] = int(value) if value else 4097
                elif key == "analysis":
                    self._project_data["analysis"] = value

            # Detecta seção de configurações
            if ctx.stripped == "configurations :":
                break  # Configurações vêm depois, processamos em streaming

        # Segunda passada: busca analysis_path que pode estar em qualquer lugar do arquivo
        if not self._project_data.get("analysis"):
            await self._find_analysis_path()

    async def _find_analysis_path(self):
        """
        Busca o analysis_path no arquivo do projeto.

        A linha 'analysis : .\\BD.ana\\BD.wda' pode estar em qualquer lugar do arquivo,
        geralmente após a seção de elementos. Esta busca é otimizada para parar assim
        que encontrar.
        """
        async for ctx in read_lines(self.project_file):
            # analysis está sempre com indent baixo (nível do projeto)
            if ctx.indent <= 2 and ctx.is_key_value:
                key, value = ctx.parse_key_value()
                if key == "analysis" and value:
                    self._project_data["analysis"] = value
                    return  # Encontrou, pode parar

    async def _create_project(self) -> Project:
        """Cria objeto Project com metadados extraidos."""
        original_name = self._project_data.get("name", self.project_file.stem)

        # If workspace_id provided, append to name for uniqueness
        # This transformation happens HERE, not in CLI
        if self.workspace_id:
            project_name = f"{original_name}_{self.workspace_id}"
            display_name = original_name
        else:
            project_name = original_name
            display_name = None  # No display_name needed if no workspace

        return Project(
            name=project_name,
            display_name=display_name,
            source_path=str(self.project_file),
            workspace_id=self.workspace_id,
            workspace_path=self.workspace_path,
            major_version=self._project_data.get("major_version", 28),
            minor_version=self._project_data.get("minor_version", 0),
            project_type=self._project_data.get("type", 4097),
            analysis_path=self._project_data.get("analysis"),
            configurations=[],  # Será preenchido depois
            status=ProjectStatus.IMPORTING,
            total_elements=0,
            elements_by_type={},
        )

    async def _stream_elements(self, project: Project):
        """Processa elementos em streaming e salva em batches."""
        self._state = ParserState.INITIAL

        async for ctx in read_lines(self.project_file):
            self.stats.lines_processed = ctx.line_number

            # Callback de progresso a cada 1000 linhas
            if ctx.line_number % 1000 == 0 and self.on_progress:
                self.on_progress(
                    ctx.line_number,
                    self.stats.total_lines,
                    self.stats.elements_found
                )

            # Máquina de estados
            await self._process_line(ctx, project)

        # Callback final
        if self.on_progress:
            self.on_progress(
                self.stats.total_lines,
                self.stats.total_lines,
                self.stats.elements_found
            )

    async def _process_line(self, ctx: LineContext, project: Project):
        """Processa uma linha baseado no estado atual."""

        # Detecta início de seções (apenas no nível do projeto, não aninhadas)
        # Seções do projeto têm indent baixo (< 3)
        if ctx.stripped == "configurations :" and ctx.indent < 3:
            self._state = ParserState.IN_CONFIGURATIONS
            self._section_indent = ctx.indent
            return

        if ctx.stripped == "elements :" and ctx.indent < 3:
            self._state = ParserState.IN_ELEMENTS
            self._section_indent = ctx.indent
            self._element_indent = -1  # Reset para detectar próximo -
            return

        # Detecta secao code_elements no nivel do projeto
        if ctx.stripped == "code_elements :" and ctx.indent < 3:
            self._state = ParserState.IN_CODE_ELEMENTS
            self._code_elements_indent = ctx.indent
            return

        # Processa baseado no estado
        if self._state == ParserState.IN_CONFIGURATIONS:
            await self._process_configuration_line(ctx, project)

        elif self._state in (ParserState.IN_ELEMENTS, ParserState.IN_ELEMENT_CONFIGS):
            await self._process_element_line(ctx, project)

        elif self._state == ParserState.IN_CODE_ELEMENTS:
            self._process_code_elements_line(ctx)

    async def _process_configuration_line(self, ctx: LineContext, project: Project):
        """Processa linha dentro da seção configurations."""

        # Fim da seção (nova seção de mesmo nível ou menor)
        if ctx.indent <= self._section_indent and ctx.stripped and not ctx.is_list_item:
            if ":" in ctx.stripped:
                self._state = ParserState.INITIAL
                # Salva última config
                if self._current_config:
                    self._save_configuration(project)
                return

        # Novo item de configuração
        if ctx.is_list_item:
            # Salva config anterior
            if self._current_config:
                self._save_configuration(project)
            self._current_config = {}
            return

        # Propriedade da configuração
        if ctx.is_key_value:
            key, value = ctx.parse_key_value()
            self._current_config[key] = value

    def _save_configuration(self, project: Project):
        """Salva configuração atual no projeto."""
        if not self._current_config.get("name"):
            return

        config = ProjectConfiguration(
            name=self._current_config.get("name", ""),
            configuration_id=self._current_config.get("configuration_id", ""),
            type=int(self._current_config.get("type", 0)),
            generation_directory=self._current_config.get("generation_directory"),
            generation_name=self._current_config.get("generation_name"),
            version=self._current_config.get("version"),
            language=int(self._current_config.get("language", 15)),
        )
        project.configurations.append(config)
        self.stats.configurations_found += 1
        self._current_config = {}

    async def _process_element_line(self, ctx: LineContext, project: Project):
        """Processa linha dentro da seção elements."""

        # Fim da seção
        if ctx.indent <= self._section_indent and ctx.stripped and not ctx.is_list_item:
            if ":" in ctx.stripped:
                self._state = ParserState.DONE
                # Salva último elemento
                if self._current_element.is_valid():
                    await self._add_element_to_batch(project)
                return

        # Novo item de elemento (apenas no nível correto)
        if ctx.is_list_item:
            # Primeiro - define o nível dos elementos
            if self._element_indent == -1:
                self._element_indent = ctx.indent

            # Ignora - aninhados (ex: configurations dentro do elemento)
            if ctx.indent != self._element_indent:
                # Pode ser início de item de configuração do elemento
                if self._state == ParserState.IN_ELEMENT_CONFIGS:
                    self._process_element_config_item(ctx)
                return

            # Salva elemento anterior
            if self._current_element.is_valid():
                await self._add_element_to_batch(project)
            self._current_element = ElementInfo()
            # Reset do estado de configurações do elemento
            self._state = ParserState.IN_ELEMENTS
            self._element_config_indent = -1
            self._current_element_config_id = ""
            self._in_element_config_item = False
            return

        # Detecta seção configurations aninhada no elemento
        if ctx.stripped == "configurations :" and ctx.indent > self._element_indent:
            self._state = ParserState.IN_ELEMENT_CONFIGS
            self._element_config_indent = ctx.indent
            return

        # Processa configurações do elemento
        if self._state == ParserState.IN_ELEMENT_CONFIGS:
            self._process_element_config_line(ctx)
            # Se ainda está em IN_ELEMENT_CONFIGS, a linha foi processada
            # Se mudou para IN_ELEMENTS, precisa continuar processando (ex: novo elemento)
            if self._state == ParserState.IN_ELEMENT_CONFIGS:
                return

        # Propriedade do elemento
        if ctx.is_key_value:
            key, value = ctx.parse_key_value()

            if key == "name":
                self._current_element.name = value
            elif key == "identifier":
                self._current_element.identifier = value
            elif key == "type":
                self._current_element.windev_type = int(value) if value else None
            elif key == "physical_name":
                self._current_element.physical_name = value

    def _process_element_config_item(self, ctx: LineContext):
        """Processa início de novo item na lista de configurações do elemento."""
        # Novo item de configuração - salva o anterior se tinha excluded
        if self._current_element_config_id and self._in_element_config_item:
            # Se chegou aqui, é porque não teve excluded:true, então não adiciona
            pass
        # Reset para novo item
        self._current_element_config_id = ""
        self._in_element_config_item = True

    def _process_element_config_line(self, ctx: LineContext):
        """Processa linha dentro da seção configurations do elemento."""
        # Fim da seção de configs do elemento
        # Caso 1: voltou para indent do elemento com propriedade (ex: report:)
        # Caso 2: encontrou '-' no nível do elemento (próximo elemento)
        if ctx.indent <= self._element_config_indent and ctx.stripped:
            if not ctx.is_list_item:
                # Propriedade do elemento (ex: report:)
                self._state = ParserState.IN_ELEMENTS
                return
            elif ctx.is_list_item and ctx.indent == self._element_indent:
                # Início do próximo elemento - sai da seção de configs
                # O processamento do '-' será feito pelo caller
                self._state = ParserState.IN_ELEMENTS
                return

        # Propriedade da configuração do elemento
        if ctx.is_key_value and self._in_element_config_item:
            key, value = ctx.parse_key_value()

            if key == "configuration_id":
                self._current_element_config_id = value
            elif key == "excluded" and value.lower() == "true":
                # Marca como excluído desta configuração
                if self._current_element_config_id:
                    self._current_element.excluded_from.append(self._current_element_config_id)

    async def _add_element_to_batch(self, project: Project):
        """Adiciona elemento ao batch e salva se necessário."""
        element = self._create_element(project, self._current_element)
        if element:
            self._element_batch.append(element)
            self.stats.elements_found += 1

            # Salva batch se atingiu tamanho
            if len(self._element_batch) >= self.BATCH_SIZE:
                await self._save_batch(project)

    def _read_source_file(self, file_path: Path) -> str:
        """
        Lê conteúdo do arquivo fonte.

        Args:
            file_path: Caminho do arquivo a ser lido

        Returns:
            Conteúdo do arquivo como string, ou string vazia em caso de erro
        """
        if not file_path.exists():
            return ""

        try:
            return file_path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            logger.warning(f"Erro ao ler {file_path}: {e}")
            return ""

    def _create_element(self, project: Project, info: ElementInfo) -> Optional[Element]:
        """Cria objeto Element a partir de ElementInfo."""
        if not info.is_valid():
            return None

        # Determina tipo
        source_type = ElementType.UNKNOWN
        if info.windev_type and info.windev_type in WINDEV_TYPE_MAP:
            source_type = WINDEV_TYPE_MAP[info.windev_type]
        else:
            ext = Path(info.physical_name).suffix.lower()
            source_type = EXTENSION_TYPE_MAP.get(ext, ElementType.UNKNOWN)

        # Determina camada
        layer = TYPE_LAYER_MAP.get(source_type)

        # Resolve caminho do arquivo e lê conteúdo
        file_path = self.project_dir / info.physical_name.lstrip(".\\").replace("\\", "/")
        raw_content = self._read_source_file(file_path)

        return Element(
            project_id=project.id,
            source_type=source_type,
            source_name=info.name,
            source_file=info.physical_name,
            windev_type=info.windev_type,
            identifier=info.identifier,
            layer=layer,
            raw_content=raw_content,
            dependencies=ElementDependencies(),
            conversion=ElementConversion(),
            excluded_from=info.excluded_from,
        )

    async def _save_batch(self, project: Project):
        """Salva batch de elementos no MongoDB."""
        if not self._element_batch:
            return

        try:
            await Element.insert_many(self._element_batch)
            self.stats.elements_saved += len(self._element_batch)
        except Exception as e:
            self.stats.errors.append({
                "batch_size": len(self._element_batch),
                "error": str(e)
            })

        self._element_batch = []

    async def _count_elements_by_type(self, project: Project) -> dict[str, int]:
        """Conta elementos por tipo no banco."""
        # Usa query direta com $id para Link references do Beanie
        elements = await Element.find({"project_id.$id": project.id}).to_list()
        counts: dict[str, int] = {}
        for el in elements:
            type_name = el.source_type.value if el.source_type else "unknown"
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts

    def _extract_project_code_element(self, project: Project) -> Optional[Element]:
        """
        Cria Element de Project Code a partir dos dados extraidos da secao code_elements.

        O Project Code contem constantes globais, variaveis globais e codigo de
        inicializacao que afeta todo o projeto.

        Args:
            project: Projeto pai

        Returns:
            Element com windev_type=0 se code_elements foi encontrado, None caso contrario
        """
        if not self._code_elements_data.get("code"):
            return None

        # type_code deve ser 0 para Project Code
        type_code = self._code_elements_data.get("type_code", 0)
        if type_code != 0:
            logger.warning(f"code_elements tem type_code={type_code}, esperado 0")
            return None

        raw_content = self._code_elements_data["code"]

        # Remove workspace suffix do nome do projeto se existir
        base_name = project.name.split("_")[0] if "_" in project.name else project.name

        return Element(
            project_id=project.id,
            source_type=ElementType.UNKNOWN,  # Tipo especial para Project Code
            source_name=f"{base_name}_ProjectCode",
            source_file=self.project_file.name,
            windev_type=0,  # Marcador de Project Code
            layer=ElementLayer.BUSINESS,  # Camada logica
            raw_content=raw_content,
            dependencies=ElementDependencies(),
            conversion=ElementConversion(),
        )

    def _process_code_elements_line(self, ctx: LineContext):
        """Processa linha dentro da secao code_elements."""
        # Fim da secao (nova secao de mesmo nivel ou menor)
        if ctx.indent <= self._code_elements_indent and ctx.stripped and ":" in ctx.stripped:
            # Finaliza code block se estava em um
            if self._in_code_block and self._code_block_content:
                self._code_elements_data["code"] = "\n".join(self._code_block_content)
            self._state = ParserState.DONE
            return

        # Detecta inicio de code block (|1+ ou similar)
        if ctx.stripped.startswith("|"):
            self._in_code_block = True
            self._code_block_content = []
            return

        # Dentro do code block - acumula linhas
        if self._in_code_block:
            # Preserva conteudo original (com indentacao relativa)
            self._code_block_content.append(ctx.line.rstrip())
            return

        # Propriedades da code_elements
        if ctx.is_key_value:
            key, value = ctx.parse_key_value()
            if key == "type_code":
                self._code_elements_data["type_code"] = int(value) if value else 0


async def map_project_elements(
    project_file: Path,
    on_progress: Optional[callable] = None,
    workspace_id: Optional[str] = None,
    workspace_path: Optional[str] = None,
) -> tuple[Project, MappingStats]:
    """
    Função de conveniência para mapear elementos de um projeto.

    Args:
        project_file: Caminho do arquivo .wwp ou .wdp
        on_progress: Callback de progresso
        workspace_id: ID do workspace (8 hex chars) para associar ao projeto
        workspace_path: Caminho do diretorio do workspace

    Returns:
        Tupla (Project, MappingStats)
    """
    mapper = ProjectElementMapper(
        project_file,
        on_progress,
        workspace_id=workspace_id,
        workspace_path=workspace_path,
    )
    return await mapper.map()
