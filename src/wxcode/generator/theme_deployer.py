"""
Theme Asset Deployer - Copia assets de tema para o diretório static do projeto gerado.

Resolve o problema de 404 em CSS, JS, fonts e images ao executar conversões
com temas Bootstrap como DashLite.
"""

from dataclasses import dataclass, field
from pathlib import Path
import shutil
import logging

logger = logging.getLogger(__name__)


@dataclass
class ThemeAssetStats:
    """Estatísticas de assets de um tema."""

    css_count: int = 0
    js_count: int = 0
    fonts_count: int = 0
    images_count: int = 0

    @property
    def total(self) -> int:
        """Total de arquivos."""
        return self.css_count + self.js_count + self.fonts_count + self.images_count

    def to_dict(self) -> dict[str, int]:
        """Converte para dicionário."""
        return {
            "css": self.css_count,
            "js": self.js_count,
            "fonts": self.fonts_count,
            "images": self.images_count,
            "total": self.total,
        }


@dataclass
class DeployResult:
    """Resultado do deploy de assets."""

    theme: str
    output_dir: Path
    files_copied: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    stats: ThemeAssetStats = field(default_factory=ThemeAssetStats)

    @property
    def success(self) -> bool:
        """Se o deploy foi bem-sucedido."""
        return len(self.errors) == 0 and len(self.files_copied) > 0


# Diretório padrão para temas (relativo ao projeto wxcode)
DEFAULT_THEMES_DIR = "themes"

# Mapeamento de diretórios de assets
ASSET_DIRS = {
    "css": "css",
    "js": "js",
    "fonts": "fonts",
    "images": "images",
}


def get_theme_path(theme: str, themes_dir: Path | None = None) -> Path | None:
    """
    Encontra o caminho do tema.

    Busca o tema no diretório de temas, suportando nomes com versão
    (ex: 'dashlite' encontra 'dashlite-v3.3.0').

    Args:
        theme: Nome do tema (ex: 'dashlite' ou 'dashlite-v3.3.0')
        themes_dir: Diretório base de temas. Se None, usa DEFAULT_THEMES_DIR.

    Returns:
        Path do tema ou None se não encontrado
    """
    if themes_dir is None:
        # Encontrar raiz do projeto wxcode
        current = Path(__file__).resolve()
        # Subir até encontrar o diretório 'themes'
        for parent in current.parents:
            candidate = parent / DEFAULT_THEMES_DIR
            if candidate.exists() and candidate.is_dir():
                themes_dir = candidate
                break
        if themes_dir is None:
            return None

    # Tentar nome exato primeiro
    exact_path = themes_dir / theme
    if exact_path.exists() and exact_path.is_dir():
        return exact_path

    # Buscar por prefixo (ex: 'dashlite' -> 'dashlite-v3.3.0')
    for theme_dir in themes_dir.iterdir():
        if theme_dir.is_dir() and theme_dir.name.startswith(f"{theme}-"):
            return theme_dir

    return None


def list_themes(themes_dir: Path | None = None) -> list[str]:
    """
    Lista temas disponíveis no diretório de temas.

    Args:
        themes_dir: Diretório base de temas. Se None, usa DEFAULT_THEMES_DIR.

    Returns:
        Lista de nomes de temas
    """
    if themes_dir is None:
        current = Path(__file__).resolve()
        for parent in current.parents:
            candidate = parent / DEFAULT_THEMES_DIR
            if candidate.exists() and candidate.is_dir():
                themes_dir = candidate
                break
        if themes_dir is None:
            return []

    return sorted(
        d.name for d in themes_dir.iterdir()
        if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
    )


def get_theme_asset_stats(theme_path: Path) -> ThemeAssetStats:
    """
    Conta assets de um tema.

    Args:
        theme_path: Caminho do diretório do tema

    Returns:
        ThemeAssetStats com contagens
    """
    stats = ThemeAssetStats()

    for asset_type, subdir in ASSET_DIRS.items():
        asset_path = theme_path / subdir
        if asset_path.exists() and asset_path.is_dir():
            count = sum(1 for f in asset_path.rglob("*") if f.is_file())
            setattr(stats, f"{asset_type}_count", count)

    return stats


def deploy_theme_assets(
    theme: str,
    output_dir: Path,
    themes_dir: Path | None = None,
    overwrite: bool = True,
) -> DeployResult:
    """
    Copia assets do tema para o diretório static do projeto gerado.

    Args:
        theme: Nome do tema (ex: 'dashlite')
        output_dir: Diretório raiz do projeto gerado
        themes_dir: Diretório base de temas. Se None, usa DEFAULT_THEMES_DIR.
        overwrite: Se True, sobrescreve arquivos existentes

    Returns:
        DeployResult com detalhes da operação
    """
    result = DeployResult(theme=theme, output_dir=output_dir)

    # Encontrar tema
    theme_path = get_theme_path(theme, themes_dir)
    if theme_path is None:
        available = list_themes(themes_dir)
        result.errors.append(
            f"Tema '{theme}' não encontrado. "
            f"Disponíveis: {', '.join(available) if available else 'nenhum'}"
        )
        return result

    logger.info(f"Usando tema: {theme_path}")

    # Diretório static do projeto gerado
    static_dir = output_dir / "app" / "static"
    if not static_dir.exists():
        result.errors.append(
            f"Diretório static não existe: {static_dir}. "
            "Execute 'wxcode init-project' primeiro."
        )
        return result

    # Copiar cada tipo de asset
    for asset_type, subdir in ASSET_DIRS.items():
        src_dir = theme_path / subdir
        dst_dir = static_dir / subdir

        if not src_dir.exists():
            logger.debug(f"Diretório não existe, pulando: {src_dir}")
            continue

        # Garantir que o diretório destino existe
        dst_dir.mkdir(parents=True, exist_ok=True)

        # Copiar arquivos recursivamente
        for src_file in src_dir.rglob("*"):
            if src_file.is_file():
                # Manter estrutura de subdiretórios
                relative = src_file.relative_to(src_dir)
                dst_file = dst_dir / relative

                # Criar subdiretórios se necessário
                dst_file.parent.mkdir(parents=True, exist_ok=True)

                # Verificar se arquivo já existe
                if dst_file.exists() and not overwrite:
                    logger.debug(f"Pulando (já existe): {dst_file}")
                    continue

                try:
                    shutil.copy2(src_file, dst_file)
                    result.files_copied.append(str(relative))

                    # Atualizar estatísticas
                    count_attr = f"{asset_type}_count"
                    current = getattr(result.stats, count_attr)
                    setattr(result.stats, count_attr, current + 1)

                    logger.debug(f"Copiado: {src_file} -> {dst_file}")

                except (OSError, shutil.Error) as e:
                    error_msg = f"Erro ao copiar {src_file}: {e}"
                    result.errors.append(error_msg)
                    logger.warning(error_msg)

    if result.success:
        logger.info(
            f"Deploy concluído: {result.stats.total} arquivos copiados "
            f"({result.stats.css_count} CSS, {result.stats.js_count} JS, "
            f"{result.stats.fonts_count} fonts, {result.stats.images_count} images)"
        )
    else:
        logger.warning(f"Deploy com problemas: {len(result.errors)} erros")

    return result
