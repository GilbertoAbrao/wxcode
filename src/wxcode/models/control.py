"""
Model de Controle de UI.

Representa um controle de interface (botão, input, célula, etc.)
extraído de páginas, janelas ou relatórios WinDev/WebDev.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Union

from beanie import Document, Link, PydanticObjectId
from pydantic import BaseModel, Field, field_validator


class DataBindingType(str, Enum):
    """Tipos de binding entre controle e dados."""

    SIMPLE = "simple"       # Binding direto TABLE.FIELD
    COMPLEX = "complex"     # Binding via relacionamento (TABLE1.FK.TABLE2.FIELD)
    VARIABLE = "variable"   # Binding com variável WLanguage (:gsVariavel)


class DataBindingInfo(BaseModel):
    """
    Informação de binding entre controle UI e dados.

    Em WinDev/WebDev, controles podem ser vinculados diretamente
    a campos de tabelas do banco de dados. Isso permite sincronização
    automática via FileToScreen() e ScreenToFile().
    """

    binding_type: DataBindingType = Field(
        default=DataBindingType.SIMPLE,
        description="Tipo de binding"
    )

    # Binding simples: TABLE.FIELD
    table_name: Optional[str] = Field(
        default=None,
        description="Nome da tabela vinculada (ex: CLIENTE)"
    )
    field_name: Optional[str] = Field(
        default=None,
        description="Nome do campo vinculado (ex: nome)"
    )

    # Binding complexo: caminho através de FKs
    binding_path: Optional[list[str]] = Field(
        default=None,
        description="Caminho de binding complexo (ex: ['PEDIDO', 'cliente_id', 'CLIENTE', 'nome'])"
    )

    # Binding com variável
    variable_name: Optional[str] = Field(
        default=None,
        description="Nome da variável vinculada (sem o prefixo ':')"
    )

    # Metadados
    source: str = Field(
        default="pdf",
        description="Fonte da informação: 'pdf' ou 'wwh'"
    )
    raw_value: Optional[str] = Field(
        default=None,
        description="Valor bruto extraído (para debug)"
    )

    @property
    def full_binding(self) -> str:
        """Retorna binding completo como string."""
        if self.binding_type == DataBindingType.VARIABLE:
            return f":{self.variable_name}" if self.variable_name else ""
        elif self.table_name and self.field_name:
            return f"{self.table_name}.{self.field_name}"
        elif self.binding_path:
            return " -> ".join(self.binding_path)
        return ""

from wxcode.models.control_type import ControlTypeDefinition
from wxcode.models.project import Project

if TYPE_CHECKING:
    from wxcode.models.element import Element


class ControlEvent(BaseModel):
    """
    Evento de um controle.

    Representa um evento como OnClick, OnChange, etc.
    com seu código WLanguage associado.
    """

    type_code: int = Field(
        ...,
        description="Código numérico do tipo de evento (ex: 851994)"
    )
    event_name: Optional[str] = Field(
        default=None,
        description="Nome do evento (ex: OnClick, OnChange)"
    )
    code: Optional[str] = Field(
        default=None,
        description="Código WLanguage do evento"
    )
    role: Optional[str] = Field(
        default=None,
        description="Papel do evento: B=Browser, S=Server"
    )
    enabled: bool = Field(
        default=True,
        description="Se o evento está habilitado"
    )


class ControlProperties(BaseModel):
    """
    Propriedades visuais de um controle.

    Extraídas do PDF de documentação.
    """

    height: Optional[int] = Field(default=None, description="Altura em pixels")
    width: Optional[int] = Field(default=None, description="Largura em pixels")
    x_position: Optional[int] = Field(default=None, description="Posição X")
    y_position: Optional[int] = Field(default=None, description="Posição Y")
    visible: bool = Field(default=True, description="Visível")
    enabled: bool = Field(default=True, description="Habilitado")
    input_type: Optional[str] = Field(
        default=None,
        description="Tipo de input (Text, Password, Email, etc.)"
    )
    style: Optional[str] = Field(default=None, description="Estilo CSS ou nome de estilo")
    tooltip: Optional[str] = Field(default=None, description="Tooltip/Hint")
    html_class: Optional[str] = Field(default=None, description="Classes CSS")
    anchor: Optional[str] = Field(default=None, description="Ancoragem")
    plane: Optional[str] = Field(default=None, description="Plano/Camada do controle (pode ser múltiplos: '1,2,3')")
    tab_order: Optional[int] = Field(default=None, description="Ordem de tabulação")

    caption: Optional[str] = Field(default=None, description="Texto/Caption do controle")
    hint_text: Optional[str] = Field(default=None, description="Placeholder/Hint")
    required: bool = Field(default=False, description="Campo obrigatório")
    read_only: bool = Field(default=False, description="Somente leitura")

    @field_validator('visible', 'enabled', 'required', 'read_only', mode='before')
    @classmethod
    def parse_bool(cls, v: Any) -> bool:
        """Converte valores variados para boolean."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ('true', 'yes', 'sim', '1', 'on')
        if isinstance(v, (int, float)):
            return bool(v)
        return False

    @field_validator('anchor', 'style', 'tooltip', 'html_class', 'caption', 'hint_text', 'input_type', 'plane', mode='before')
    @classmethod
    def parse_string(cls, v: Any) -> Optional[str]:
        """Converte valores variados para string (plane pode vir como int do MongoDB antigo)."""
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            # Converte dict para string JSON-like
            return str(v)
        return str(v)


class Control(Document):
    """
    Representa um controle de UI de um elemento WinDev/WebDev.

    Cada controle é um documento separado no MongoDB para permitir
    queries eficientes e navegação hierárquica.
    """

    # Relacionamentos principais
    element_id: PydanticObjectId = Field(
        ...,
        description="ID do Element pai (PAGE, WINDOW, REPORT)"
    )
    project_id: PydanticObjectId = Field(
        ...,
        description="ID do Project"
    )

    # Tipo (Link para tabela de tipos)
    type_code: int = Field(
        ...,
        description="Código numérico do tipo (fonte: campo 'type' do .wwh)"
    )
    type_definition_id: Optional[PydanticObjectId] = Field(
        default=None,
        description="ID da definição de tipo"
    )

    # Identificação
    name: str = Field(
        ...,
        description="Nome do controle (ex: EDT_LOGIN, BTN_Salvar)"
    )
    full_path: str = Field(
        ...,
        description="Caminho completo (ex: CELL_Main.CELL_Form.EDT_Login)"
    )

    # Hierarquia
    parent_control_id: Optional[PydanticObjectId] = Field(
        default=None,
        description="ID do controle pai (para controles aninhados)"
    )
    children_ids: list[PydanticObjectId] = Field(
        default_factory=list,
        description="IDs dos controles filhos"
    )
    depth: int = Field(
        default=0,
        description="Nível na hierarquia (0 = raiz)"
    )

    # Dados extraídos
    properties: Optional[ControlProperties] = Field(
        default=None,
        description="Propriedades visuais do PDF (None se órfão)"
    )
    events: list[ControlEvent] = Field(
        default_factory=list,
        description="Eventos do arquivo .wwh/.wdw"
    )
    raw_properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Todas propriedades brutas do PDF"
    )

    # Código WLanguage associado
    code_blocks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Blocos de código WLanguage do controle"
    )

    # Dados originais do .wwh
    windev_internal_properties: Optional[str] = Field(
        default=None,
        description="Campo internal_properties original (base64)"
    )

    # Data Binding (vinculação com dados)
    data_binding: Optional[DataBindingInfo] = Field(
        default=None,
        description="Informação de binding entre controle e campo de tabela"
    )
    is_bound: bool = Field(
        default=False,
        description="True se o controle tem binding com dados"
    )

    # Flags
    is_orphan: bool = Field(
        default=False,
        description="True se existe no .wwh mas não no PDF"
    )
    is_container: bool = Field(
        default=False,
        description="True se pode conter outros controles"
    )
    has_code: bool = Field(
        default=False,
        description="True se tem código WLanguage associado"
    )

    # Metadados
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "controls"
        use_state_management = True
        indexes = [
            "element_id",
            "project_id",
            "name",
            "type_code",
            "parent_control_id",
            "is_orphan",
            "is_container",
            "has_code",
            "is_bound",
            [("element_id", 1), ("name", 1)],       # Único composto
            [("element_id", 1), ("depth", 1)],      # Para queries hierárquicas
            [("element_id", 1), ("type_code", 1)],  # Busca por tipo
            [("element_id", 1), ("is_bound", 1)],   # Busca por binding
        ]

    def __str__(self) -> str:
        return f"Control({self.name}, type={self.type_code}, depth={self.depth})"

    async def get_type_definition(self) -> Optional[ControlTypeDefinition]:
        """Carrega a definição de tipo do controle."""
        if self.type_definition_id:
            return await ControlTypeDefinition.get(self.type_definition_id)
        return await ControlTypeDefinition.find_one(
            ControlTypeDefinition.type_code == self.type_code
        )

    async def get_children(self) -> list["Control"]:
        """Carrega controles filhos."""
        return await Control.find(
            Control.parent_control_id == self.id
        ).sort("+name").to_list()

    async def get_parent(self) -> Optional["Control"]:
        """Carrega controle pai."""
        if self.parent_control_id:
            return await Control.get(self.parent_control_id)
        return None

    async def get_siblings(self) -> list["Control"]:
        """Carrega controles irmãos (mesmo pai)."""
        return await Control.find(
            Control.element_id == self.element_id,
            Control.parent_control_id == self.parent_control_id,
            Control.id != self.id
        ).sort("+name").to_list()

    async def get_ancestors(self) -> list["Control"]:
        """Carrega todos os ancestrais até a raiz."""
        ancestors = []
        current = await self.get_parent()
        while current:
            ancestors.append(current)
            current = await current.get_parent()
        return ancestors

    async def get_descendants(self) -> list["Control"]:
        """Carrega todos os descendentes recursivamente."""
        descendants = []
        children = await self.get_children()
        for child in children:
            descendants.append(child)
            descendants.extend(await child.get_descendants())
        return descendants

    @property
    def has_events(self) -> bool:
        """Verifica se o controle tem eventos."""
        return len(self.events) > 0

    @property
    def has_properties(self) -> bool:
        """Verifica se o controle tem propriedades visuais."""
        return self.properties is not None

    def get_event_by_name(self, event_name: str) -> Optional[ControlEvent]:
        """Busca um evento pelo nome."""
        for event in self.events:
            if event.event_name == event_name:
                return event
        return None

    def get_events_with_code(self) -> list[ControlEvent]:
        """Retorna apenas eventos que têm código associado."""
        return [e for e in self.events if e.code]


# Mapeamento de type codes para nomes de eventos (curado manualmente)
EVENT_TYPE_CODES: dict[int, str] = {
    851994: "OnClick",
    852016: "OnInit",
    852017: "OnChange",
    852018: "OnExit",
    852019: "OnEntry",
    852020: "OnModify",
    852021: "OnDoubleClick",
    852022: "OnKeyDown",
    852023: "OnKeyUp",
    852024: "OnMouseOver",
    852025: "OnMouseOut",
    852026: "OnFocus",
    852027: "OnBlur",
    852028: "OnSubmit",
    852029: "OnLoad",
    852030: "OnUnload",
    852031: "OnScroll",
    852032: "OnResize",
    # Adicionar mais conforme curadoria
}


def get_event_name(type_code: int) -> str:
    """
    Retorna o nome do evento para um type_code.

    Args:
        type_code: Código numérico do tipo de evento

    Returns:
        Nome do evento ou 'event_{code}' se não mapeado
    """
    return EVENT_TYPE_CODES.get(type_code, f"event_{type_code}")
