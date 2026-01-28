"""
Model de definição de tipo de controle.

Tabela dinâmica que armazena os tipos de controles encontrados
durante o parsing dos arquivos .wwh/.wdw.
"""

from datetime import datetime
from typing import Optional

from beanie import Document
from pydantic import Field


class ControlTypeDefinition(Document):
    """
    Tabela dinâmica de tipos de controles.

    Novos tipos são adicionados automaticamente quando encontrados
    durante o parsing dos arquivos WinDev/WebDev.

    O type_code vem do campo 'type' do arquivo .wwh/.wdw e é a
    fonte da verdade para identificação do tipo.
    """

    # Identificação (do campo 'type' do .wwh/.wdw)
    type_code: int = Field(
        ...,
        description="Código numérico do tipo (fonte: campo 'type' do .wwh)"
    )

    # Nome do tipo
    type_name: Optional[str] = Field(
        default=None,
        description="Nome do tipo definido manualmente (ex: 'Edit', 'Button')"
    )
    inferred_name: Optional[str] = Field(
        default=None,
        description="Nome inferido pelo prefixo do controle (ex: EDT_ → 'Edit')"
    )

    # Comportamento
    is_container: bool = Field(
        default=False,
        description="True se pode conter outros controles (CELL, ZONE, TAB, etc.)"
    )

    # Metadados
    first_seen_in: Optional[str] = Field(
        default=None,
        description="Nome do elemento onde o tipo foi encontrado pela primeira vez"
    )
    occurrences: int = Field(
        default=0,
        description="Quantidade de controles deste tipo encontrados"
    )
    example_names: list[str] = Field(
        default_factory=list,
        description="Exemplos de nomes de controles deste tipo (max 5)"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "control_types"
        use_state_management = True
        indexes = [
            [("type_code", 1)],  # Índice único para busca por código
        ]

    def __str__(self) -> str:
        return f"ControlType({self.type_code}, name={self.display_name})"

    @property
    def display_name(self) -> str:
        """Retorna o nome para exibição do tipo."""
        return self.type_name or self.inferred_name or f"type_{self.type_code}"

    def add_example(self, control_name: str) -> None:
        """Adiciona um exemplo de nome de controle (max 5)."""
        if control_name not in self.example_names and len(self.example_names) < 5:
            self.example_names.append(control_name)

    def increment_occurrences(self) -> None:
        """Incrementa contador de ocorrências."""
        self.occurrences += 1
        self.updated_at = datetime.utcnow()


# Mapeamento de prefixos para inferência de nomes de tipos
# Fonte: project-refs/WX_CodeStyle_Prefixes.md
PREFIX_TO_TYPE_NAME: dict[str, str] = {
    # === Window Controls ===
    "DOTNET_": "DotNet",
    "ACTB_": "ActionBar",
    "ABZ_": "ActionBarZone",
    "AX_": "ActiveX",
    "ADV_": "Advertising",
    "BAC_": "BarCode",
    "BCOD_": "BarCode",
    "BTN_": "Button",
    "CAL_": "Calendar",
    "CAM_": "Camera",
    "STC_": "Static",
    "CAR_": "Carousel",
    "CELL_": "Cell",
    "CHART_": "Chart",
    "CBOX_": "CheckBox",
    "CODEEDT_": "CodeEditor",
    "COMBO_": "ComboBox",
    "CONF_": "Conference",
    "CTPL_": "ControlTemplate",
    "CUBE_": "Cube",
    "DASH_": "Dashboard",
    "DIAGEDT_": "DiagramEditor",
    "DOPA_": "DockablePanel",
    "DRW_": "Drawer",
    "EDT_": "Edit",
    "FLEX_": "Flexbox",
    "WIRE_": "GraphicLink",
    "GRID_": "Grid",
    "RIBGRP_": "RibbonGroup",
    "GR_": "GroupOfControls",
    "COL_": "Column",
    "HTM_": "HTML",
    "HTMEDT_": "HTMLEditor",
    "IMG_": "Image",
    "IE_": "ImageEditor",
    "PROGBAR_": "ProgressBar",
    "IWC_": "InternalWindow",
    "KANBAN_": "Kanban",
    "LIST_": "List",
    "LAYOUT_": "Layout",
    "LSV_": "ListView",
    "LOOP_": "Looper",
    "ATT_": "LooperAttribute",
    "BRK_": "LooperBreak",
    "MAP_": "Map",
    "MENU_": "Menu",
    "OPT_": "MenuOption",
    "MZ_": "MultilineZone",
    "MM_": "Multimedia",
    "NATIVE_": "NativeContainer",
    "OLE_": "OLE",
    "ORGA_": "OrganizationChart",
    "ORG_": "Organizer",
    "PDF_": "PDFReader",
    "PVT_": "PivotTable",
    "RADIO_": "RadioButton",
    "RGS_": "RangeSlider",
    "NOTE_": "Rating",
    "RIBBON_": "Ribbon",
    "SLD_": "Slider",
    "SCH_": "Scheduler",
    "SCROLL_": "Scrollbar",
    "SB_": "SegmentedButton",
    "SPLIT_": "Splitter",
    "SHA_": "Shape",
    "SHAPE_": "Shape",
    "SIDE_": "Sidebar",
    "SPIN_": "Spin",
    "PSHEET_": "Spreadsheet",
    "SBC_": "StatusBarCell",
    "STREAM_": "Stream",
    "SC_": "Supercontrol",
    "TAB_": "Tab",
    "TABLE_": "Table",
    "TL_": "TimeLine",
    "TBAR_": "Toolbar",
    "TMAP_": "TreeMap",
    "TREE_": "TreeView",
    "TVT_": "TreeViewTable",
    "VAL_": "PivotTableValue",
    "WEBDEV_": "WebDevPage",
    "WP_": "WordProcessing",

    # === Page Controls (WebDev) ===
    "SMP_": "Breadcrumb",
    "CPTCH_": "Captcha",
    "HS_": "Drawer",
    "FLASH_": "Flash",
    "FSTC_": "FormattedStatic",
    "HTMSTC_": "HTMLStatic",
    "IFRM_": "IFrame",
    "IPAGE_": "InternalPage",
    "JAVA_": "JavaApplet",
    "ZONE_": "LayoutZone",
    "HR_": "HorizontalRule",
    "SLI_": "LinearSlider",
    "LINK_": "Link",
    "NAV_": "NavigationBar",
    "PGR_": "Pager",
    "PEEL_": "PeelingCorner",
    "POPUP_": "Popup",
    "RSLI_": "RangeSlider",
    "MARK_": "Rating",
    "RTA_": "RichTextArea",
    "SL_": "Silverlight",
    "SM_": "SiteMap",
    "BAN_": "SlidingBanner",
    "SOC_": "SocialNetwork",
    "THUMB_": "Thumbnail",
    "HTABLE_": "TreeViewTable",
    "UPL_": "Upload",
    "VIDEO_": "Video",
    "CMP_": "WebComponent",

    # === Project Elements ===
    "TPLC_": "ControlTemplate",
    "TLM_": "Telemetry",
    "AID_": "DocumentHelp",
    "MODEL_": "DocumentModel",
    "QRY_": "Query",
    "RPT_": "Report",
    "RPTTPL_": "ReportTemplate",
    "BRO_": "BrowserProcedures",
    "SET_": "ProcedureSet",
    "PAGE_": "Page",
    "PAGETPL_": "PageTemplate",
    "STYLE_": "StyleSheet",
    "WS_": "WebService",
    "PLAN_": "ActionPlan",
    "REST_": "RESTWebService",
    "PIC_": "Picture",
    "IW_": "InternalWindow",
    "WIN_": "Window",
    "WINTPL_": "WindowTemplate",
    "TEST_": "Test",

    # === Report Controls ===
    "CALC_": "Calculation",
    "GANTT_": "GanttChart",
    "RPTI_": "InternalReport",
    "ITEM_": "Item",
    "DEF_": "Preset",
    "RTF_": "RTF",
    "SIG_": "Signature",
    "SRPT_": "Subreport",

    # === Variações comuns encontradas em projetos reais ===
    "stc_": "Static",  # lowercase
    "FORM_": "Form",
    "DASHBOARD_": "Dashboard",
    "LNK_": "Link",
}

# Prefixos conhecidos como containers (podem ter filhos)
CONTAINER_PREFIXES: set[str] = {
    # Containers básicos
    "CELL_",
    "ZONE_",
    "TAB_",
    "LOOP_",
    "POPUP_",
    "MENU_",
    "LAYOUT_",

    # Containers de navegação/organização
    "RIBBON_",
    "RIBGRP_",
    "TBAR_",
    "DRW_",
    "HS_",
    "SIDE_",
    "NAV_",
    "DASH_",

    # Containers de dados
    "TABLE_",
    "TVT_",
    "HTABLE_",
    "TREE_",
    "KANBAN_",
    "PVT_",
    "ORGA_",
    "ORG_",
    "SCH_",

    # Containers de página/janela
    "IWC_",
    "IPAGE_",
    "SC_",
    "CTPL_",
    "GR_",

    # Page/Form containers
    "PAGE_",
    "FORM_",
    "WIN_",
}


def infer_type_name_from_prefix(control_name: str) -> Optional[str]:
    """
    Infere o nome do tipo a partir do prefixo do controle.

    Args:
        control_name: Nome do controle (ex: EDT_LOGIN, BTN_Salvar)

    Returns:
        Nome inferido do tipo ou None se não reconhecido
    """
    for prefix, type_name in PREFIX_TO_TYPE_NAME.items():
        if control_name.startswith(prefix):
            return type_name
    return None


def is_container_by_prefix(control_name: str) -> bool:
    """
    Verifica se o controle é um container baseado no prefixo.

    Args:
        control_name: Nome do controle

    Returns:
        True se o prefixo indica que é um container
    """
    for prefix in CONTAINER_PREFIXES:
        if control_name.startswith(prefix):
            return True
    return False
