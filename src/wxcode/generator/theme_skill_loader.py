"""
Theme Skill Loader para carregar skills de tema baseado nos componentes necessários.

Analisa controles de um Element e carrega apenas os skills relevantes do tema,
implementando progressive discovery para otimização de tokens.
"""

from pathlib import Path
from typing import Any
import yaml
import logging

from wxcode.models.control import Control

logger = logging.getLogger(__name__)


# Mapeamento de type_code WinDev → componente de skill
# Baseado em ControlTypeDefinition.type_code
CONTROL_TYPE_TO_COMPONENT: dict[int, str | None] = {
    # Tipo 1: Static/Label - não precisa de skill específico
    1: None,

    # Tipo 2: Image
    2: None,

    # Tipo 3: Button
    3: "buttons",

    # Tipo 4: Edit/Input
    4: "forms/input",

    # Tipo 5: Radio Button
    5: "forms/checkbox",

    # Tipo 6: Check Box
    6: "forms/checkbox",

    # Tipo 7: Combo Box
    7: "forms/select",

    # Tipo 8: List Box
    8: "forms/select",

    # Tipo 9: Table
    9: "tables",

    # Tipo 10: Looper
    10: "tables",

    # Tipo 11: Tab
    11: "cards",  # Tabs geralmente são dentro de cards

    # Tipo 12: TreeView
    12: None,

    # Tipo 13: Progress Bar
    13: None,

    # Tipo 14: Slider
    14: "forms/input",

    # Tipo 15: Scheduler
    15: None,

    # Tipo 16: Chart
    16: None,

    # Tipo 17: Rich Text
    17: "forms/textarea",

    # Tipo 18: HTML Control
    18: None,

    # Tipo 19: Popup Menu
    19: "modals",

    # Tipo 20: Toolbar
    20: "buttons",

    # Tipos de Container
    21: "layout",  # Cell
    22: "layout",  # Super Control
    23: "layout",  # Internal Window

    # Tipo 65538: Page (container principal)
    65538: "layout",

    # Tipo 65539: Browser code area
    65539: None,

    # Tipo 65540: Cell
    65540: "layout",

    # Tipo 65541: Template
    65541: "layout",
}

# Mapeamento por nome de tipo (fallback quando type_code não mapeado)
CONTROL_NAME_TO_COMPONENT: dict[str, str | None] = {
    "button": "buttons",
    "btn": "buttons",
    "edit": "forms/input",
    "edt": "forms/input",
    "input": "forms/input",
    "static": None,
    "sta": None,
    "label": None,
    "lbl": None,
    "table": "tables",
    "tbl": "tables",
    "looper": "tables",
    "loop": "tables",
    "combo": "forms/select",
    "cmb": "forms/select",
    "list": "forms/select",
    "lst": "forms/select",
    "check": "forms/checkbox",
    "chk": "forms/checkbox",
    "radio": "forms/checkbox",
    "rad": "forms/checkbox",
    "cell": "layout",
    "cel": "layout",
    "tab": "cards",
    "image": None,
    "img": None,
    "popup": "modals",
    "modal": "modals",
    "rich": "forms/textarea",
    "memo": "forms/textarea",
    "txt": "forms/textarea",
    "link": "buttons",
    "lnk": "buttons",
    "date": "forms/datepicker",
    "calendar": "forms/datepicker",
    "time": "forms/datepicker",
    "datetime": "forms/datepicker",
}

# Mapeamento por input_type do ControlProperties
INPUT_TYPE_TO_COMPONENT: dict[str, str] = {
    "date": "forms/datepicker",
    "datetime": "forms/datepicker",
    "datetime-local": "forms/datepicker",
    "time": "forms/datepicker",
    "month": "forms/datepicker",
    "week": "forms/datepicker",
    "email": "forms/input",
    "password": "forms/input",
    "number": "forms/input",
    "tel": "forms/input",
    "url": "forms/input",
    "text": "forms/input",
    "search": "forms/input",
    "textarea": "forms/textarea",
    "multiline": "forms/textarea",
}


class ThemeSkillLoader:
    """
    Carrega skills de tema baseado nos componentes necessários.

    Implementa progressive discovery: analisa os controles de uma página
    e carrega apenas os skills relevantes para minimizar uso de tokens.

    Attributes:
        theme: Nome do tema (ex: 'dashlite', 'hyper')
        skills_path: Caminho para a pasta de skills do tema
    """

    # Diretório padrão para skills (relativo ao projeto)
    DEFAULT_SKILLS_DIR = ".claude/skills/themes"

    def __init__(
        self,
        theme: str,
        skills_base_path: Path | None = None,
        project_root: Path | None = None,
    ):
        """
        Inicializa o loader de skills.

        Args:
            theme: Nome do tema (deve corresponder a uma pasta em skills_base_path)
            skills_base_path: Caminho base para os skills de tema.
                            Se None, usa project_root/.claude/skills/themes
            project_root: Raiz do projeto. Se None, usa o cwd.
        """
        self.theme = theme

        if skills_base_path:
            self.skills_path = skills_base_path / theme
        else:
            root = project_root or Path.cwd()
            self.skills_path = root / self.DEFAULT_SKILLS_DIR / theme

        self._loaded_skills: dict[str, str] = {}  # Cache de skills carregados
        self._skill_metadata: dict[str, dict[str, Any]] = {}  # Metadados dos skills

    def theme_exists(self) -> bool:
        """Verifica se o tema existe."""
        return self.skills_path.exists() and self.skills_path.is_dir()

    def list_available_themes(self) -> list[str]:
        """Lista temas disponíveis no diretório de skills."""
        themes_dir = self.skills_path.parent
        if not themes_dir.exists():
            return []
        return [
            d.name for d in themes_dir.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        ]

    def get_theme_description(self) -> str | None:
        """Retorna a descrição do tema do _index.md."""
        index_path = self.skills_path / "_index.md"
        if not index_path.exists():
            return None

        content = index_path.read_text(encoding="utf-8")
        metadata = self._parse_frontmatter(content)
        return metadata.get("description")

    def analyze_required_components(
        self,
        controls: list[Control],
    ) -> set[str]:
        """
        Analisa controles e retorna os componentes necessários.

        Args:
            controls: Lista de controles de um Element

        Returns:
            Set de nomes de componentes (ex: {'buttons', 'forms/input', 'tables'})
        """
        components: set[str] = set()

        for control in controls:
            component = self._map_control_to_component(control)
            if component:
                components.add(component)

        return components

    def _map_control_to_component(self, control: Control) -> str | None:
        """
        Mapeia um controle para seu componente de skill.

        Args:
            control: Controle a ser mapeado

        Returns:
            Nome do componente ou None se não precisar de skill
        """
        # 1. Tentar por type_code primeiro (mais preciso)
        if control.type_code in CONTROL_TYPE_TO_COMPONENT:
            component = CONTROL_TYPE_TO_COMPONENT[control.type_code]

            # Verificar input_type para casos especiais (datepicker, etc.)
            if component == "forms/input" and control.properties:
                input_type = control.properties.input_type
                if input_type and input_type.lower() in INPUT_TYPE_TO_COMPONENT:
                    return INPUT_TYPE_TO_COMPONENT[input_type.lower()]

            return component

        # 2. Fallback por prefixo do nome do controle
        control_name = control.name.lower()
        for prefix, component in CONTROL_NAME_TO_COMPONENT.items():
            if control_name.startswith(prefix + "_") or control_name.startswith(prefix):

                # Verificar input_type para casos especiais
                if component == "forms/input" and control.properties:
                    input_type = control.properties.input_type
                    if input_type and input_type.lower() in INPUT_TYPE_TO_COMPONENT:
                        return INPUT_TYPE_TO_COMPONENT[input_type.lower()]

                return component

        # 3. Sem mapeamento encontrado
        logger.debug(f"No component mapping for control: {control.name} (type_code={control.type_code})")
        return None

    def load_skills(self, components: set[str]) -> str:
        """
        Carrega e concatena os skills dos componentes.

        Sempre carrega _index.md primeiro. Para componentes em subpastas
        (ex: forms/input), carrega também o _index.md da pasta pai.

        Args:
            components: Set de componentes a carregar

        Returns:
            String concatenada de todos os skills relevantes
        """
        if not self.theme_exists():
            raise ValueError(
                f"Theme '{self.theme}' not found at {self.skills_path}. "
                f"Available themes: {self.list_available_themes()}"
            )

        skills_content: list[str] = []
        loaded: set[str] = set()

        # 1. Sempre carrega _index.md do tema primeiro
        index_content = self._load_skill("_index.md")
        if index_content:
            skills_content.append(index_content)
            loaded.add("_index")

        # 2. Carrega skills dos componentes e suas dependências
        for component in sorted(components):  # Ordenar para consistência
            self._load_skill_with_deps(component, loaded, skills_content)

        # Concatenar com separadores
        return "\n\n---\n\n".join(skills_content)

    def _load_skill_with_deps(
        self,
        component: str,
        loaded: set[str],
        skills_content: list[str],
    ) -> None:
        """
        Carrega um skill e suas dependências.

        Args:
            component: Nome do componente (ex: 'buttons', 'forms/input')
            loaded: Set de skills já carregados
            skills_content: Lista para acumular conteúdo
        """
        if component in loaded:
            return

        # Para componentes em subpastas, carregar _index da pasta primeiro
        if "/" in component:
            parent_dir = component.rsplit("/", 1)[0]
            parent_index = f"{parent_dir}/_index"
            if parent_index not in loaded:
                parent_index_content = self._load_skill(f"{parent_dir}/_index.md")
                if parent_index_content:
                    skills_content.append(parent_index_content)
                    loaded.add(parent_index)

        # Carregar o skill do componente
        skill_file = f"{component}.md"
        content = self._load_skill(skill_file)
        if content:
            skills_content.append(content)
            loaded.add(component)

            # Carregar dependências declaradas no frontmatter
            metadata = self._skill_metadata.get(skill_file, {})
            for dep in metadata.get("depends-on", []):
                # Remover prefixo do tema se presente (ex: 'dashlite-buttons' -> 'buttons')
                dep_clean = dep.replace(f"{self.theme}-", "").replace("_index", "_index")
                if dep_clean not in loaded:
                    self._load_skill_with_deps(dep_clean, loaded, skills_content)

    def _load_skill(self, relative_path: str) -> str | None:
        """
        Carrega um arquivo de skill.

        Args:
            relative_path: Caminho relativo à pasta do tema

        Returns:
            Conteúdo do skill ou None se não existir
        """
        # Verificar cache
        if relative_path in self._loaded_skills:
            return self._loaded_skills[relative_path]

        skill_path = self.skills_path / relative_path
        if not skill_path.exists():
            logger.debug(f"Skill not found: {skill_path}")
            return None

        try:
            content = skill_path.read_text(encoding="utf-8")

            # Parsear frontmatter para metadados
            metadata = self._parse_frontmatter(content)
            self._skill_metadata[relative_path] = metadata

            # Cachear
            self._loaded_skills[relative_path] = content

            return content

        except Exception as e:
            logger.warning(f"Error loading skill {skill_path}: {e}")
            return None

    def _parse_frontmatter(self, content: str) -> dict[str, Any]:
        """
        Parseia frontmatter YAML do skill.

        Args:
            content: Conteúdo completo do arquivo

        Returns:
            Dicionário com metadados ou {}
        """
        if not content.startswith("---"):
            return {}

        try:
            # Encontrar fim do frontmatter
            end_idx = content.find("---", 3)
            if end_idx == -1:
                return {}

            frontmatter = content[3:end_idx].strip()
            return yaml.safe_load(frontmatter) or {}

        except yaml.YAMLError as e:
            logger.warning(f"Error parsing frontmatter: {e}")
            return {}

    async def load_skills_for_element(
        self,
        element_id: str,
    ) -> str:
        """
        Carrega skills necessários para um Element específico.

        Busca todos os controles do Element no MongoDB e carrega
        os skills relevantes.

        Args:
            element_id: ID do Element (ObjectId string)

        Returns:
            String concatenada de skills
        """
        from bson import ObjectId

        # Buscar controles do elemento
        controls = await Control.find(
            Control.element_id == ObjectId(element_id)
        ).to_list()

        if not controls:
            logger.warning(f"No controls found for element {element_id}")
            # Retorna apenas o _index do tema
            return self._load_skill("_index.md") or ""

        # Analisar componentes necessários
        components = self.analyze_required_components(controls)

        logger.info(
            f"Element {element_id}: {len(controls)} controls -> "
            f"components: {sorted(components)}"
        )

        # Carregar skills
        return self.load_skills(components)

    def get_all_skills(self) -> str:
        """
        Carrega todos os skills do tema.

        Útil para testes ou quando queremos o contexto completo.

        Returns:
            String concatenada de todos os skills
        """
        if not self.theme_exists():
            raise ValueError(f"Theme '{self.theme}' not found")

        all_components: set[str] = set()

        # Encontrar todos os arquivos .md
        for md_file in self.skills_path.rglob("*.md"):
            relative = md_file.relative_to(self.skills_path)
            # Converter para formato de componente (sem .md)
            component = str(relative.with_suffix("")).replace("\\", "/")
            # Pular _index files (serão carregados automaticamente)
            if not component.endswith("_index"):
                all_components.add(component)

        return self.load_skills(all_components)


def get_available_themes(project_root: Path | None = None) -> list[dict[str, str]]:
    """
    Lista todos os temas disponíveis com descrições.

    Args:
        project_root: Raiz do projeto. Se None, usa cwd.

    Returns:
        Lista de dicts com 'name' e 'description'
    """
    root = project_root or Path.cwd()
    themes_dir = root / ThemeSkillLoader.DEFAULT_SKILLS_DIR

    if not themes_dir.exists():
        return []

    themes = []
    for theme_dir in themes_dir.iterdir():
        if theme_dir.is_dir() and not theme_dir.name.startswith("_"):
            loader = ThemeSkillLoader(theme_dir.name, project_root=root)
            themes.append({
                "name": theme_dir.name,
                "description": loader.get_theme_description() or "No description",
            })

    return sorted(themes, key=lambda t: t["name"])
