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
    "TerminalAskUserQuestionMessage",
    # Progress messages (for chat display)
    "TerminalTaskCreateMessage",
    "TerminalTaskUpdateMessage",
    "TerminalFileWriteMessage",
    "TerminalFileEditMessage",
    "TerminalSummaryMessage",
    "TerminalBashMessage",
    "TerminalFileReadMessage",
    "TerminalTaskSpawnMessage",
    "TerminalGlobMessage",
    "TerminalGrepMessage",
    "TerminalBannerMessage",
    # Helper models
    "AskUserQuestionItem",
    "AskUserQuestionOption",
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


class AskUserQuestionOption(BaseModel):
    """Opcao para uma pergunta AskUserQuestion."""

    label: str = Field(..., description="Texto da opcao")
    description: str | None = Field(default=None, description="Descricao da opcao")


class AskUserQuestionItem(BaseModel):
    """Uma pergunta individual do AskUserQuestion."""

    question: str = Field(..., description="Texto da pergunta")
    header: str | None = Field(default=None, description="Header/titulo da pergunta")
    options: list[AskUserQuestionOption] = Field(
        default_factory=list,
        description="Opcoes disponiveis",
    )
    multiSelect: bool = Field(
        default=False,
        description="Se permite selecao multipla",
    )


class TerminalAskUserQuestionMessage(BaseModel):
    """
    Mensagem de pergunta do Claude para o usuario.

    Enviada quando o Claude usa a ferramenta AskUserQuestion.
    O frontend deve exibir no chat e permitir que o usuario responda.
    """

    type: Literal["ask_user_question"] = "ask_user_question"
    tool_use_id: str = Field(
        ...,
        description="ID do tool_use para correlacionar a resposta",
    )
    questions: list[AskUserQuestionItem] = Field(
        ...,
        description="Lista de perguntas a serem exibidas",
    )
    timestamp: str | None = Field(
        default=None,
        description="Timestamp do evento",
    )


# =============================================================================
# Progress Messages (for chat display)
# =============================================================================


class TerminalTaskCreateMessage(BaseModel):
    """
    Mensagem de criacao de tarefa.

    Enviada quando o Claude cria uma nova tarefa via TaskCreate.
    O frontend exibe no chat para mostrar progresso.
    """

    type: Literal["task_create"] = "task_create"
    tool_use_id: str = Field(..., description="ID do tool_use")
    subject: str = Field(..., description="Titulo da tarefa")
    description: str = Field(default="", description="Descricao da tarefa")
    active_form: str = Field(default="", description="Forma ativa (ex: 'Criando...')")
    timestamp: str | None = Field(default=None, description="Timestamp do evento")


class TerminalTaskUpdateMessage(BaseModel):
    """
    Mensagem de atualizacao de tarefa.

    Enviada quando o Claude atualiza o status de uma tarefa via TaskUpdate.
    O frontend exibe no chat para mostrar progresso.
    """

    type: Literal["task_update"] = "task_update"
    tool_use_id: str = Field(..., description="ID do tool_use")
    task_id: str = Field(..., description="ID da tarefa")
    status: str = Field(..., description="Novo status (in_progress, completed)")
    subject: str = Field(default="", description="Titulo da tarefa (se disponivel)")
    timestamp: str | None = Field(default=None, description="Timestamp do evento")


class TerminalFileWriteMessage(BaseModel):
    """
    Mensagem de criacao de arquivo.

    Enviada quando o Claude cria um novo arquivo via Write.
    O frontend exibe no chat para mostrar progresso.
    """

    type: Literal["file_write"] = "file_write"
    tool_use_id: str = Field(..., description="ID do tool_use")
    file_path: str = Field(..., description="Caminho completo do arquivo")
    file_name: str = Field(..., description="Nome do arquivo (sem caminho)")
    timestamp: str | None = Field(default=None, description="Timestamp do evento")


class TerminalFileEditMessage(BaseModel):
    """
    Mensagem de edicao de arquivo.

    Enviada quando o Claude edita um arquivo via Edit.
    O frontend exibe no chat para mostrar progresso.
    """

    type: Literal["file_edit"] = "file_edit"
    tool_use_id: str = Field(..., description="ID do tool_use")
    file_path: str = Field(..., description="Caminho completo do arquivo")
    file_name: str = Field(..., description="Nome do arquivo (sem caminho)")
    timestamp: str | None = Field(default=None, description="Timestamp do evento")


class TerminalSummaryMessage(BaseModel):
    """
    Mensagem de resumo da sessao.

    Enviada quando ha um resumo da sessao no arquivo JSONL.
    O frontend exibe no chat como destaque.
    """

    type: Literal["summary"] = "summary"
    summary: str = Field(..., description="Texto do resumo")
    timestamp: str | None = Field(default=None, description="Timestamp do evento")


class TerminalBashMessage(BaseModel):
    """
    Mensagem de execucao de comando Bash.

    Enviada quando o Claude executa um comando via Bash.
    O frontend exibe no chat para mostrar progresso.
    """

    type: Literal["bash"] = "bash"
    tool_use_id: str = Field(..., description="ID do tool_use")
    command: str = Field(..., description="Comando executado")
    description: str = Field(default="", description="Descricao do comando")
    timestamp: str | None = Field(default=None, description="Timestamp do evento")


class TerminalFileReadMessage(BaseModel):
    """
    Mensagem de leitura de arquivo.

    Enviada quando o Claude le um arquivo via Read.
    O frontend exibe no chat para mostrar progresso.
    """

    type: Literal["file_read"] = "file_read"
    tool_use_id: str = Field(..., description="ID do tool_use")
    file_path: str = Field(..., description="Caminho completo do arquivo")
    file_name: str = Field(..., description="Nome do arquivo (sem caminho)")
    timestamp: str | None = Field(default=None, description="Timestamp do evento")


class TerminalTaskSpawnMessage(BaseModel):
    """
    Mensagem de spawn de agente.

    Enviada quando o Claude cria um subagente via Task.
    O frontend exibe no chat para mostrar progresso.
    """

    type: Literal["task_spawn"] = "task_spawn"
    tool_use_id: str = Field(..., description="ID do tool_use")
    description: str = Field(..., description="Descricao da tarefa")
    subagent_type: str = Field(default="", description="Tipo do subagente")
    timestamp: str | None = Field(default=None, description="Timestamp do evento")


class TerminalGlobMessage(BaseModel):
    """
    Mensagem de busca de arquivos.

    Enviada quando o Claude busca arquivos via Glob.
    O frontend exibe no chat para mostrar progresso.
    """

    type: Literal["glob"] = "glob"
    tool_use_id: str = Field(..., description="ID do tool_use")
    pattern: str = Field(..., description="Padrao de busca")
    timestamp: str | None = Field(default=None, description="Timestamp do evento")


class TerminalGrepMessage(BaseModel):
    """
    Mensagem de busca de conteudo.

    Enviada quando o Claude busca conteudo via Grep.
    O frontend exibe no chat para mostrar progresso.
    """

    type: Literal["grep"] = "grep"
    tool_use_id: str = Field(..., description="ID do tool_use")
    pattern: str = Field(..., description="Padrao de busca")
    timestamp: str | None = Field(default=None, description="Timestamp do evento")


class TerminalBannerMessage(BaseModel):
    """
    Mensagem de banner/status do Claude.

    Enviada quando o Claude exibe um banner importante como
    PROJECT INITIALIZED, PHASE COMPLETE, etc.
    O frontend exibe no chat como destaque.
    """

    type: Literal["assistant_banner"] = "assistant_banner"
    text: str = Field(..., description="Texto do banner")
    timestamp: str | None = Field(default=None, description="Timestamp do evento")


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
    TerminalAskUserQuestionMessage,
    # Progress messages
    TerminalTaskCreateMessage,
    TerminalTaskUpdateMessage,
    TerminalFileWriteMessage,
    TerminalFileEditMessage,
    TerminalSummaryMessage,
    TerminalBashMessage,
    TerminalFileReadMessage,
    TerminalTaskSpawnMessage,
    TerminalGlobMessage,
    TerminalGrepMessage,
    TerminalBannerMessage,
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
