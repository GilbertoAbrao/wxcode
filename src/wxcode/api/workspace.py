"""
API de arquivos do workspace.

Endpoints para listar e ler arquivos dentro do workspace de um produto,
com validacao de seguranca para prevenir path traversal.
"""

from pathlib import Path
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from wxcode.models.product import Product


router = APIRouter()


# === Models ===


class FileNode(BaseModel):
    """
    No de arquivo ou diretorio no workspace.

    Representa um item na arvore de arquivos, podendo ser
    arquivo ou diretorio com filhos.
    """

    name: str
    path: str  # Relativo ao workspace
    is_directory: bool
    size: Optional[int] = None
    children: Optional[list["FileNode"]] = None


class FileContent(BaseModel):
    """
    Conteudo de um arquivo.

    Inclui o conteudo textual, tamanho e tipo MIME inferido.
    """

    path: str
    content: str
    size: int
    mime_type: str


# === Helper Functions ===


# Mapeamento de extensoes para tipos MIME
MIME_TYPES = {
    # Python
    ".py": "text/x-python",
    ".pyi": "text/x-python",
    # JavaScript/TypeScript
    ".js": "text/javascript",
    ".jsx": "text/javascript",
    ".ts": "text/typescript",
    ".tsx": "text/typescript",
    ".mjs": "text/javascript",
    ".cjs": "text/javascript",
    # Web
    ".html": "text/html",
    ".htm": "text/html",
    ".css": "text/css",
    ".scss": "text/x-scss",
    ".sass": "text/x-sass",
    ".less": "text/x-less",
    # Data
    ".json": "application/json",
    ".yaml": "text/yaml",
    ".yml": "text/yaml",
    ".toml": "text/x-toml",
    ".xml": "application/xml",
    # Config
    ".env": "text/plain",
    ".ini": "text/plain",
    ".cfg": "text/plain",
    ".conf": "text/plain",
    # Docs
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".rst": "text/x-rst",
    # Shell
    ".sh": "text/x-shellscript",
    ".bash": "text/x-shellscript",
    ".zsh": "text/x-shellscript",
    # SQL
    ".sql": "text/x-sql",
    # Other
    ".dockerfile": "text/x-dockerfile",
    ".gitignore": "text/plain",
    ".editorconfig": "text/plain",
}


def _get_mime_type(file_path: Path) -> str:
    """
    Retorna tipo MIME baseado na extensao do arquivo.

    Args:
        file_path: Caminho do arquivo

    Returns:
        Tipo MIME ou 'text/plain' para extensoes desconhecidas
    """
    suffix = file_path.suffix.lower()
    name = file_path.name.lower()

    # Casos especiais por nome
    if name == "dockerfile":
        return "text/x-dockerfile"
    if name.startswith("."):
        # Arquivos ocultos como .gitignore
        return MIME_TYPES.get(name, "text/plain")

    return MIME_TYPES.get(suffix, "text/plain")


def _list_directory(target: Path, workspace: Path) -> list[FileNode]:
    """
    Lista arquivos e diretorios recursivamente.

    Args:
        target: Diretorio alvo para listar
        workspace: Raiz do workspace (para calcular caminhos relativos)

    Returns:
        Lista de FileNode representando a arvore de arquivos
    """
    nodes: list[FileNode] = []

    if not target.exists() or not target.is_dir():
        return nodes

    # Ordenar: diretorios primeiro, depois arquivos, ambos alfabeticamente
    items = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))

    for item in items:
        # Ignorar arquivos/pastas ocultos (exceto .planning que e importante)
        if item.name.startswith(".") and item.name != ".planning":
            continue

        # Ignorar __pycache__ e node_modules
        if item.name in ("__pycache__", "node_modules", ".git"):
            continue

        relative_path = str(item.relative_to(workspace))

        if item.is_dir():
            children = _list_directory(item, workspace)
            nodes.append(
                FileNode(
                    name=item.name,
                    path=relative_path,
                    is_directory=True,
                    children=children,
                )
            )
        else:
            try:
                size = item.stat().st_size
            except OSError:
                size = None

            nodes.append(
                FileNode(
                    name=item.name,
                    path=relative_path,
                    is_directory=False,
                    size=size,
                )
            )

    return nodes


async def _get_product_workspace(product_id: str) -> tuple[Product, Path]:
    """
    Busca produto e retorna com caminho do workspace validado.

    Args:
        product_id: ID do produto

    Returns:
        Tupla (produto, caminho_workspace)

    Raises:
        HTTPException: Se produto nao encontrado ou workspace invalido
    """
    try:
        product_oid = PydanticObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de produto invalido")

    product = await Product.get(product_oid)
    if not product:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    workspace = Path(product.workspace_path)
    if not workspace.exists():
        raise HTTPException(status_code=404, detail="Workspace nao encontrado")

    return product, workspace


def _validate_path_security(target: Path, workspace: Path) -> None:
    """
    Valida que o caminho alvo esta dentro do workspace.

    Previne ataques de path traversal (ex: ../../etc/passwd).

    Args:
        target: Caminho alvo a validar
        workspace: Raiz do workspace

    Raises:
        HTTPException 403: Se caminho esta fora do workspace
    """
    try:
        resolved = target.resolve()
        workspace_resolved = workspace.resolve()

        if not resolved.is_relative_to(workspace_resolved):
            raise HTTPException(status_code=403, detail="Caminho fora do workspace")
    except ValueError:
        raise HTTPException(status_code=403, detail="Caminho fora do workspace")


# === Endpoints ===


@router.get("/products/{product_id}/files", response_model=list[FileNode])
async def list_workspace_files(
    product_id: str,
    path: str = Query(default="", description="Caminho relativo dentro do workspace"),
) -> list[FileNode]:
    """
    Lista arquivos no workspace de um produto.

    Retorna arvore de arquivos e diretorios recursivamente.
    Ignora arquivos ocultos (exceto .planning), __pycache__ e node_modules.

    Args:
        product_id: ID do produto
        path: Caminho relativo dentro do workspace (padrao: raiz)

    Returns:
        Lista de FileNode representando a arvore

    Raises:
        403: Se path tenta acessar fora do workspace
        404: Se produto ou workspace nao encontrado
    """
    product, workspace = await _get_product_workspace(product_id)

    # Calcular caminho alvo
    target = workspace / path if path else workspace

    # Validacao de seguranca
    _validate_path_security(target, workspace)

    if not target.exists():
        raise HTTPException(status_code=404, detail="Caminho nao encontrado")

    if not target.is_dir():
        raise HTTPException(status_code=400, detail="Caminho nao e um diretorio")

    return _list_directory(target, workspace)


@router.get("/products/{product_id}/files/content", response_model=FileContent)
async def read_workspace_file(
    product_id: str,
    path: str = Query(..., description="Caminho relativo do arquivo"),
) -> FileContent:
    """
    Le conteudo de um arquivo do workspace.

    Limite de 1MB para prevenir problemas de memoria.
    Arquivos maiores devem ser baixados diretamente.

    Args:
        product_id: ID do produto
        path: Caminho relativo do arquivo

    Returns:
        FileContent com conteudo, tamanho e tipo MIME

    Raises:
        403: Se path tenta acessar fora do workspace
        404: Se arquivo nao encontrado
        413: Se arquivo maior que 1MB
    """
    product, workspace = await _get_product_workspace(product_id)

    # Calcular caminho do arquivo
    file_path = workspace / path

    # Validacao de seguranca
    _validate_path_security(file_path, workspace)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Caminho nao e um arquivo")

    # Verificar tamanho
    size = file_path.stat().st_size
    if size > 1_000_000:  # 1MB
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo muito grande ({size:,} bytes). Limite: 1MB"
        )

    # Ler conteudo
    try:
        content = file_path.read_text(errors="replace")
    except UnicodeDecodeError:
        # Fallback para arquivos binarios
        raise HTTPException(
            status_code=400,
            detail="Arquivo binario nao pode ser exibido como texto"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler arquivo: {e}")

    mime_type = _get_mime_type(file_path)

    return FileContent(
        path=path,
        content=content,
        size=size,
        mime_type=mime_type,
    )
