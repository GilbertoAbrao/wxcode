"""SpecContextLoader - Carrega specs das dependências para fornecer contexto ao LLM."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import Element


class SpecContextLoader:
    """Carrega specs arquivadas das dependências de um elemento."""

    def __init__(self, specs_dir: Path | None = None):
        """Inicializa o loader.

        Args:
            specs_dir: Diretório de specs. Default: openspec/specs/
        """
        if specs_dir is None:
            # Assume que estamos no diretório do projeto
            specs_dir = Path("openspec/specs")
        self.specs_dir = specs_dir

    def load_dependency_specs(self, element: "Element") -> tuple[list[str], list[str]]:
        """Carrega specs das dependências do elemento.

        Args:
            element: Elemento com dependencies.uses preenchido

        Returns:
            Tuple de (specs_content, missing_deps):
            - specs_content: Lista de conteúdos das specs encontradas
            - missing_deps: Lista de dependências sem spec
        """
        specs_content: list[str] = []
        missing_deps: list[str] = []

        if not element.dependencies or not element.dependencies.uses:
            return specs_content, missing_deps

        for dep_name in element.dependencies.uses:
            spec_content = self._load_spec(dep_name)
            if spec_content:
                specs_content.append(spec_content)
            else:
                missing_deps.append(dep_name)

        return specs_content, missing_deps

    def _load_spec(self, element_name: str) -> str | None:
        """Carrega spec de um elemento específico.

        Args:
            element_name: Nome do elemento (ex: PAGE_Login, classUsuario)

        Returns:
            Conteúdo da spec ou None se não encontrada
        """
        # Normaliza nome para formato de spec
        spec_name = self._normalize_spec_name(element_name)
        spec_path = self.specs_dir / f"{spec_name}-spec" / "spec.md"

        if spec_path.exists():
            return self._format_spec(element_name, spec_path.read_text())

        # Tenta variações do nome
        variations = [
            f"{spec_name.lower()}-spec",
            f"{spec_name.replace('_', '-').lower()}-spec",
            f"convert-{spec_name.lower()}",
        ]

        for variation in variations:
            alt_path = self.specs_dir / variation / "spec.md"
            if alt_path.exists():
                return self._format_spec(element_name, alt_path.read_text())

        return None

    def _normalize_spec_name(self, name: str) -> str:
        """Normaliza nome do elemento para formato de spec.

        Args:
            name: Nome original (ex: PAGE_Login, classUsuario)

        Returns:
            Nome normalizado (ex: page-login, class-usuario)
        """
        # Remove prefixos comuns
        prefixes = ["PAGE_", "class", "TABLE:", "proc:"]
        result = name
        for prefix in prefixes:
            if result.startswith(prefix):
                result = result[len(prefix):]
                break

        # Converte camelCase para kebab-case
        import re
        result = re.sub(r"([a-z])([A-Z])", r"\1-\2", result)

        # Converte underscores para hifens e lowercase
        result = result.replace("_", "-").lower()

        # Adiciona prefixo de tipo se tinha
        if name.startswith("PAGE_"):
            result = f"page-{result}"
        elif name.startswith("class"):
            result = f"class-{result}"
        elif name.startswith("TABLE:"):
            result = f"table-{result}"
        elif name.startswith("proc:"):
            result = f"proc-{result}"

        return result

    def _format_spec(self, element_name: str, content: str) -> str:
        """Formata spec para inclusão no contexto.

        Args:
            element_name: Nome do elemento
            content: Conteúdo da spec

        Returns:
            Spec formatada com header
        """
        return f"""
## Spec: {element_name}

{content}

---
"""

    def format_context(
        self, specs_content: list[str], missing_deps: list[str]
    ) -> str:
        """Formata contexto completo para o LLM.

        Args:
            specs_content: Specs carregadas
            missing_deps: Dependências sem spec

        Returns:
            Contexto formatado
        """
        parts = []

        if specs_content:
            parts.append("# Specs das Dependências Convertidas\n")
            parts.append(
                "As seguintes dependências já foram convertidas. "
                "Use essas specs como referência para manter consistência.\n"
            )
            parts.extend(specs_content)

        if missing_deps:
            parts.append("\n# Dependências Não Documentadas\n")
            parts.append(
                "As seguintes dependências ainda não foram convertidas. "
                "A conversão pode precisar de ajustes quando forem.\n"
            )
            for dep in missing_deps:
                parts.append(f"- {dep}\n")

        return "".join(parts)
