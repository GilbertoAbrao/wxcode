"""
Helper para captura e persistencia de session_id do Claude Code CLI.

Funcoes para extrair session_id de mensagens stream-json e salvar
atomicamente no MongoDB.
"""

import json
from typing import Optional, Union

from beanie import PydanticObjectId

from wxcode.models.output_project import OutputProject


def capture_session_id_from_line(line: Union[bytes, str]) -> Optional[str]:
    """
    Extrai session_id de uma linha de output stream-json do Claude Code CLI.

    Procura por mensagens do tipo:
    {"type":"system","subtype":"init","session_id":"uuid",...}

    Args:
        line: Linha de output em bytes ou str

    Returns:
        session_id se encontrado na mensagem init, None caso contrario
    """
    try:
        # Normaliza para string
        if isinstance(line, bytes):
            line_str = line.decode("utf-8")
        else:
            line_str = line

        # Remove whitespace
        line_str = line_str.strip()
        if not line_str:
            return None

        # Parse JSON
        data = json.loads(line_str)

        # Verifica se e mensagem init com session_id
        if (
            data.get("type") == "system"
            and data.get("subtype") == "init"
            and "session_id" in data
        ):
            return data["session_id"]

        return None

    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
        # Nao e JSON valido ou encoding invalido - normal para linhas nao-JSON
        return None


async def save_session_id_atomic(
    output_project_id: str,
    claude_session_id: str,
) -> bool:
    """
    Salva session_id atomicamente no OutputProject.

    Usa update atomico para evitar race conditions. So atualiza se
    claude_session_id ainda nao estiver definido.

    Args:
        output_project_id: ID do OutputProject (string ou ObjectId)
        claude_session_id: Session ID do Claude Code CLI

    Returns:
        True se atualizou, False se ja estava definido ou nao encontrou
    """
    try:
        # Converte para PydanticObjectId se necessario
        if isinstance(output_project_id, str):
            project_id = PydanticObjectId(output_project_id)
        else:
            project_id = output_project_id

        # Atomic update: so atualiza se claude_session_id e None
        result = await OutputProject.find_one(
            OutputProject.id == project_id,
            OutputProject.claude_session_id == None,  # noqa: E711
        ).update(
            {"$set": {"claude_session_id": claude_session_id}}
        )

        # Verifica se atualizou
        return result is not None and result.modified_count > 0

    except Exception:
        # Erro de conexao, ID invalido, etc
        return False
