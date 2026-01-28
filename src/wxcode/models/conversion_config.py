"""
Model para configuração de conversão por configuration específica.

Este módulo define a estrutura que encapsula parâmetros de conversão
para uma configuration específica de um projeto WinDev/WebDev.
"""

from dataclasses import dataclass
from pathlib import Path

from bson import ObjectId


@dataclass
class ConversionConfig:
    """Configuração para uma conversão de projeto por configuration.

    Attributes:
        project_id: ID do projeto no MongoDB.
        project_name: Nome do projeto.
        configuration_name: Nome da configuration (ex: "Producao", "API_Homolog").
        configuration_id: ID da configuration para filtrar elementos.
        config_type: Tipo da configuration (2=Site, 23=API REST, 17=Library, 1=Exe).
        output_dir: Diretório de output para esta configuration.
    """
    project_id: ObjectId
    project_name: str
    configuration_name: str
    configuration_id: str
    config_type: int
    output_dir: Path

    @property
    def is_site(self) -> bool:
        """Verifica se é uma configuration de Site WebDev.

        Returns:
            True se config_type == 2 (Site WEBDEV).
        """
        return self.config_type == 2

    @property
    def is_api_only(self) -> bool:
        """Verifica se é uma configuration de API REST apenas.

        Returns:
            True se config_type == 23 (REST Webservice).
        """
        return self.config_type == 23

    @property
    def is_library(self) -> bool:
        """Verifica se é uma configuration de Library.

        Returns:
            True se config_type == 17 (Library).
        """
        return self.config_type == 17

    @property
    def is_executable(self) -> bool:
        """Verifica se é uma configuration de Windows Executable.

        Returns:
            True se config_type == 1 (Windows Exe).
        """
        return self.config_type == 1

    @property
    def should_generate_templates(self) -> bool:
        """Determina se deve gerar templates Jinja2.

        Returns:
            True se for Site (type=2), False para API only, Library ou Exe.
        """
        return self.is_site

    @property
    def should_generate_routes(self) -> bool:
        """Determina se deve gerar rotas FastAPI.

        Returns:
            True se for Site ou API (types 2 ou 23).
        """
        return self.is_site or self.is_api_only

    def __str__(self) -> str:
        """Representação string da configuração.

        Returns:
            String descritiva da configuration.
        """
        type_name = {
            2: "Site WEBDEV",
            23: "REST Webservice",
            17: "Library",
            1: "Windows Exe"
        }.get(self.config_type, f"Unknown ({self.config_type})")

        return f"{self.configuration_name} ({type_name}) → {self.output_dir}"
