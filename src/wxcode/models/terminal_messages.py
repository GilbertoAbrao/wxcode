"""
Modelos Pydantic para mensagens WebSocket do terminal interativo.

Define tipos de mensagem para comunicacao bidirecional entre frontend e backend
usando discriminated union pattern para validacao type-safe.
"""

from typing import Literal, Union

from pydantic import BaseModel, Field, TypeAdapter


__all__ = [
    # Incoming messages (client -> server)
    "TerminalInputMessage",
    "TerminalResizeMessage",
    "TerminalSignalMessage",
    # Outgoing messages (server -> client)
    "TerminalOutputMessage",
    "TerminalStatusMessage",
    "TerminalErrorMessage",
    "TerminalClosedMessage",
    # Union types
    "IncomingMessage",
    "OutgoingMessage",
    # Parser function
    "parse_incoming_message",
]


# =============================================================================
# Incoming Messages (Client -> Server)
# =============================================================================


class TerminalInputMessage(BaseModel):
    """
    Mensagem de entrada do usuario para o terminal.

    Enviada pelo frontend quando o usuario digita no terminal.
    O campo data contem os caracteres digitados (pode incluir sequencias de escape).
    """

    type: Literal["input"] = "input"
    data: str = Field(
        ...,
        max_length=2048,
        description="Dados de entrada do usuario (max 2KB para corresponder a MAX_MESSAGE_SIZE)",
    )


class TerminalResizeMessage(BaseModel):
    """
    Mensagem de redimensionamento do terminal.

    Enviada pelo frontend quando o tamanho da janela do terminal muda.
    As dimensoes sao em linhas e colunas (caracteres), nao pixels.
    """

    type: Literal["resize"] = "resize"
    rows: int = Field(
        ...,
        ge=1,
        le=500,
        description="Numero de linhas do terminal (1-500)",
    )
    cols: int = Field(
        ...,
        ge=1,
        le=500,
        description="Numero de colunas do terminal (1-500)",
    )


class TerminalSignalMessage(BaseModel):
    """
    Mensagem de sinal para o processo do terminal.

    Enviada pelo frontend para sinais de controle como Ctrl+C (SIGINT),
    Ctrl+D (EOF), ou terminacao graceful (SIGTERM).
    """

    type: Literal["signal"] = "signal"
    signal: Literal["SIGINT", "SIGTERM", "EOF"] = Field(
        ...,
        description="Sinal a enviar: SIGINT (Ctrl+C), SIGTERM (terminar), EOF (Ctrl+D)",
    )


# =============================================================================
# Outgoing Messages (Server -> Client)
# =============================================================================


class TerminalOutputMessage(BaseModel):
    """
    Mensagem de saida do processo para o terminal.

    Enviada pelo backend quando o processo PTY produz output (stdout/stderr).
    O frontend deve renderizar este conteudo no xterm.js.
    """

    type: Literal["output"] = "output"
    data: str = Field(
        ...,
        description="Dados de saida do processo (pode incluir sequencias ANSI)",
    )


class TerminalStatusMessage(BaseModel):
    """
    Mensagem de status da conexao WebSocket.

    Enviada pelo backend para indicar o estado da conexao.
    Usado para notificar conexao estabelecida ou reconexao a sessao existente.
    """

    type: Literal["status"] = "status"
    connected: bool = Field(
        ...,
        description="True se conectado ao backend",
    )
    session_id: str | None = Field(
        default=None,
        description="ID da sessao para reconexao (None se nova conexao)",
    )


class TerminalErrorMessage(BaseModel):
    """
    Mensagem de erro do terminal.

    Enviada pelo backend quando ocorre um erro de validacao ou processamento.
    O frontend deve exibir ao usuario sem fechar a conexao.
    """

    type: Literal["error"] = "error"
    message: str = Field(
        ...,
        description="Descricao do erro para exibir ao usuario",
    )
    code: str | None = Field(
        default=None,
        description="Codigo do erro para tratamento programatico (ex: VALIDATION, NO_SESSION)",
    )


class TerminalClosedMessage(BaseModel):
    """
    Mensagem de processo encerrado.

    Enviada pelo backend quando o processo PTY termina (normalmente ou com erro).
    O frontend deve indicar que a sessao terminou.
    """

    type: Literal["closed"] = "closed"
    exit_code: int | None = Field(
        default=None,
        description="Codigo de saida do processo (None se nao disponivel)",
    )


# =============================================================================
# Discriminated Unions
# =============================================================================


IncomingMessage = Union[
    TerminalInputMessage,
    TerminalResizeMessage,
    TerminalSignalMessage,
]
"""
Uniao discriminada de mensagens recebidas pelo servidor.

O campo 'type' e usado como discriminador para determinar o tipo de mensagem.
"""


OutgoingMessage = Union[
    TerminalOutputMessage,
    TerminalStatusMessage,
    TerminalErrorMessage,
    TerminalClosedMessage,
]
"""
Uniao discriminada de mensagens enviadas pelo servidor.

O campo 'type' e usado como discriminador para determinar o tipo de mensagem.
"""


# =============================================================================
# Parser Function
# =============================================================================


# TypeAdapter pre-criado para melhor performance (evita recriacao por mensagem)
_incoming_message_adapter: TypeAdapter[IncomingMessage] = TypeAdapter(IncomingMessage)


def parse_incoming_message(raw: dict) -> IncomingMessage:
    """
    Parseia um dict raw para uma mensagem tipada usando discriminated union.

    Args:
        raw: Dicionario com os dados da mensagem (normalmente de websocket.receive_json())

    Returns:
        Mensagem tipada (TerminalInputMessage, TerminalResizeMessage, ou TerminalSignalMessage)

    Raises:
        pydantic.ValidationError: Se o tipo for invalido ou campos obrigatorios faltarem
    """
    return _incoming_message_adapter.validate_python(raw)
