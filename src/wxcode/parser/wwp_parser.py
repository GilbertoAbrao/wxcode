"""
Parser de arquivos .wwp (projeto WebDev).

O arquivo .wwp é um YAML-like proprietário da PC Soft que contém
a estrutura do projeto e referências para todos os elementos.
"""

import re
from pathlib import Path
from typing import Any, Optional

from wxcode.models import (
    Project,
    ProjectConfiguration,
    ProjectStatus,
    Element,
    ElementType,
    ElementLayer,
    ElementDependencies,
    ElementConversion,
)


# Mapeamento de extensão para tipo de elemento
EXTENSION_TO_TYPE: dict[str, ElementType] = {
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

# Mapeamento de tipo numérico WinDev para tipo de elemento
WINDEV_TYPE_TO_ELEMENT: dict[int, ElementType] = {
    65538: ElementType.PAGE,
    65541: ElementType.PAGE_TEMPLATE,
    65539: ElementType.BROWSER_PROCEDURE,
    7: ElementType.PROCEDURE_GROUP,
    4: ElementType.CLASS,
    5: ElementType.QUERY,
    22: ElementType.WEBSERVICE,
}

# Mapeamento de tipo para camada
TYPE_TO_LAYER: dict[ElementType, ElementLayer] = {
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


class WWPParser:
    """
    Parser de arquivos .wwp (projeto WebDev).

    Extrai metadados do projeto e lista de elementos.
    """

    def __init__(self, file_path: Path):
        """
        Inicializa o parser.

        Args:
            file_path: Caminho para o arquivo .wwp
        """
        self.file_path = Path(file_path)
        self.project_dir = self.file_path.parent
        self._content: Optional[str] = None
        self._lines: Optional[list[str]] = None

    def _read_file(self) -> None:
        """Lê o conteúdo do arquivo."""
        if self._content is None:
            with open(self.file_path, "r", encoding="utf-8", errors="replace") as f:
                self._content = f.read()
            self._lines = self._content.split("\n")

    def _parse_value(self, line: str) -> tuple[str, str]:
        """
        Extrai chave e valor de uma linha.

        Args:
            line: Linha no formato "chave : valor"

        Returns:
            Tupla (chave, valor)
        """
        if " : " in line:
            parts = line.split(" : ", 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""
            # Remove aspas
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            return key, value
        return line.strip(), ""

    def _get_indent_level(self, line: str) -> int:
        """Retorna o nível de indentação da linha."""
        return len(line) - len(line.lstrip())

    async def parse(self) -> Project:
        """
        Faz o parse do arquivo .wwp e retorna o projeto.

        Returns:
            Objeto Project com metadados do projeto.
        """
        self._read_file()

        # Extrai metadados básicos
        name = self._extract_simple_value("name")
        major_version = int(self._extract_simple_value("major_version") or "26")
        minor_version = int(self._extract_simple_value("minor_version") or "0")
        project_type = int(self._extract_simple_value("type") or "4097")

        # Extrai configurações
        configurations = self._extract_configurations()

        # Conta elementos
        elements_info = self._extract_elements_info()

        # Cria projeto
        project = Project(
            name=name or self.file_path.stem,
            source_path=str(self.file_path),
            major_version=major_version,
            minor_version=minor_version,
            project_type=project_type,
            configurations=configurations,
            status=ProjectStatus.IMPORTED,
            total_elements=len(elements_info),
            elements_by_type=self._count_by_type(elements_info),
        )

        return project

    def _extract_simple_value(self, key: str) -> Optional[str]:
        """Extrai valor simples do arquivo."""
        self._read_file()

        pattern = rf"^\s*{key}\s*:\s*(.+?)$"
        for line in self._lines:
            match = re.match(pattern, line)
            if match:
                value = match.group(1).strip()
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                return value
        return None

    def _extract_configurations(self) -> list[ProjectConfiguration]:
        """Extrai configurações de build do projeto."""
        self._read_file()

        configurations = []
        in_configurations = False
        current_config: dict[str, Any] = {}
        config_indent = 0

        for i, line in enumerate(self._lines):
            stripped = line.strip()

            # Detecta seção de configurações
            if stripped == "configurations :":
                in_configurations = True
                continue

            if not in_configurations:
                continue

            # Novo item de configuração
            if stripped == "-":
                if current_config:
                    configurations.append(self._make_configuration(current_config))
                current_config = {}
                config_indent = self._get_indent_level(line)
                continue

            # Fim da seção de configurações
            indent = self._get_indent_level(line)
            if indent < config_indent and stripped and not stripped.startswith("-"):
                if current_config:
                    configurations.append(self._make_configuration(current_config))
                break

            # Propriedade da configuração
            if " : " in stripped and indent > config_indent:
                key, value = self._parse_value(stripped)
                current_config[key] = value

        # Última configuração
        if current_config:
            configurations.append(self._make_configuration(current_config))

        return configurations

    def _make_configuration(self, data: dict[str, Any]) -> ProjectConfiguration:
        """Cria objeto ProjectConfiguration a partir de dict."""
        return ProjectConfiguration(
            name=data.get("name", "Unknown"),
            configuration_id=data.get("configuration_id", ""),
            type=int(data.get("type", 0)),
            generation_directory=data.get("generation_directory"),
            generation_name=data.get("generation_name"),
            version=data.get("version"),
            language=int(data.get("language", 15)),
            **{"64bits": data.get("64bits", "true").lower() == "true"},
            linux=data.get("linux", "false").lower() == "true",
        )

    def _extract_elements_info(self) -> list[dict[str, Any]]:
        """Extrai informações básicas de todos os elementos."""
        self._read_file()

        elements = []
        in_elements = False
        current_element: dict[str, Any] = {}
        element_indent = 0

        for i, line in enumerate(self._lines):
            stripped = line.strip()

            # Detecta seção de elementos
            if stripped == "elements :":
                in_elements = True
                continue

            if not in_elements:
                continue

            # Fim da seção de elementos (nova seção de nível 0)
            if stripped and not stripped.startswith("-") and ":" in stripped:
                indent = self._get_indent_level(line)
                if indent == 0:
                    if current_element:
                        elements.append(current_element)
                    break

            # Novo elemento
            if stripped == "-":
                if current_element and "name" in current_element:
                    elements.append(current_element)
                current_element = {}
                element_indent = self._get_indent_level(line)
                continue

            # Propriedade do elemento
            if " : " in stripped:
                key, value = self._parse_value(stripped)
                if key in ["name", "identifier", "physical_name", "type"]:
                    current_element[key] = value

        # Último elemento
        if current_element and "name" in current_element:
            elements.append(current_element)

        return elements

    def _count_by_type(self, elements: list[dict[str, Any]]) -> dict[str, int]:
        """Conta elementos por tipo."""
        counts: dict[str, int] = {}

        for elem in elements:
            physical_name = elem.get("physical_name", "")
            if physical_name:
                ext = Path(physical_name).suffix.lower()
                elem_type = EXTENSION_TO_TYPE.get(ext, ElementType.UNKNOWN)
                type_name = elem_type.value
                counts[type_name] = counts.get(type_name, 0) + 1

        return counts

    async def parse_elements(self, project: Project) -> list[Element]:
        """
        Extrai todos os elementos do projeto.

        Args:
            project: Projeto pai

        Returns:
            Lista de objetos Element
        """
        elements_info = self._extract_elements_info()
        elements = []

        for info in elements_info:
            element = await self._parse_element(project, info)
            if element:
                elements.append(element)

        return elements

    async def _parse_element(
        self,
        project: Project,
        info: dict[str, Any]
    ) -> Optional[Element]:
        """
        Cria objeto Element a partir de informações extraídas.

        Args:
            project: Projeto pai
            info: Dicionário com informações do elemento

        Returns:
            Objeto Element ou None se não for válido
        """
        physical_name = info.get("physical_name", "")
        if not physical_name:
            return None

        # Determina tipo pelo extensão ou código numérico
        ext = Path(physical_name).suffix.lower()
        windev_type = int(info.get("type", 0)) if info.get("type") else None

        if windev_type and windev_type in WINDEV_TYPE_TO_ELEMENT:
            source_type = WINDEV_TYPE_TO_ELEMENT[windev_type]
        elif ext in EXTENSION_TO_TYPE:
            source_type = EXTENSION_TO_TYPE[ext]
        else:
            source_type = ElementType.UNKNOWN

        # Determina camada
        layer = TYPE_TO_LAYER.get(source_type)

        # Lê conteúdo do arquivo se existir
        raw_content = ""
        file_path = self.project_dir / physical_name.lstrip(".\\").replace("\\", "/")
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    raw_content = f.read()
            except Exception:
                pass

        return Element(
            project_id=project.id,
            source_type=source_type,
            source_name=info.get("name", ""),
            source_file=physical_name,
            windev_type=windev_type,
            identifier=info.get("identifier"),
            raw_content=raw_content,
            layer=layer,
            dependencies=ElementDependencies(),
            conversion=ElementConversion(),
        )
