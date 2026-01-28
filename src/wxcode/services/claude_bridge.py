"""
Ponte de comunicação com Claude Code.

Executa comandos no Claude Code (diretamente ou via Docker) e retorna stream de respostas.
"""

import asyncio
import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator, Optional, List, Dict, Any

from wxcode.services.token_tracker import TokenTracker
from wxcode.services.guardrail import Guardrail

logger = logging.getLogger(__name__)


def _is_docker_available() -> bool:
    """Verifica se Docker está disponível."""
    return shutil.which("docker") is not None


def _is_claude_cli_available() -> bool:
    """Verifica se Claude Code CLI está disponível diretamente."""
    return shutil.which("claude") is not None


@dataclass
class ChatMessage:
    """Mensagem de chat."""
    role: str  # "user" ou "assistant"
    content: str
    timestamp: datetime


@dataclass
class ChatSession:
    """Estado de uma sessão de chat."""
    session_id: str
    tenant_id: str
    project_id: str
    messages: List[ChatMessage]
    token_tracker: TokenTracker
    created_at: datetime


class ClaudeBridge:
    """
    Ponte de comunicação com Claude Code em containers Docker.

    Executa comandos no Claude Code usando docker exec e retorna
    stream de respostas para o cliente.

    Nota: Esta é uma implementação simplificada. Em produção,
    seria necessário usar a biblioteca docker-py para comunicação
    mais robusta com containers.
    """

    def __init__(
        self,
        tenant_id: str,
        token_tracker: Optional[TokenTracker] = None,
        use_docker: Optional[bool] = None,
    ):
        """
        Inicializa o bridge.

        Args:
            tenant_id: ID do tenant (usuário/organização)
            token_tracker: Tracker de tokens (cria novo se não fornecido)
            use_docker: Se True, usa Docker. Se False, usa CLI diretamente.
                       Se None (padrão), auto-detecta.
        """
        self.tenant_id = tenant_id
        self.container_name = f"claude-{tenant_id}"
        self.token_tracker = token_tracker or TokenTracker()

        # Auto-detectar modo de execução
        if use_docker is None:
            # Preferir CLI direto se disponível, senão tenta Docker
            self.use_docker = not _is_claude_cli_available() and _is_docker_available()
        else:
            self.use_docker = use_docker

    async def execute(
        self,
        prompt: str,
        project_id: str,
        session_id: Optional[str] = None,
        context: str = "conversion",
        allowed_tools: Optional[List[str]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executa comando no Claude Code e retorna stream de respostas.

        Args:
            prompt: Prompt a ser enviado ao Claude Code
            project_id: ID do projeto
            session_id: ID da sessão para continuar conversa existente
            context: Contexto da operação (analysis, conversion, review)
            allowed_tools: Lista de ferramentas permitidas (usa padrão do contexto se None)

        Yields:
            Dicionários com dados do stream-json do Claude Code
        """
        # Obtém ferramentas permitidas
        tools = allowed_tools or Guardrail.get_allowed_tools(context)

        print(f"[ClaudeBridge] use_docker={self.use_docker}, context={context}")

        # Monta comando base dependendo do modo
        if self.use_docker:
            cmd = [
                "docker", "exec", "-i",
                self.container_name,
                "npx", "-y", "@anthropic-ai/claude-code",
                "-p", prompt,
                "--output-format", "stream-json",
                "--verbose",  # Required when using stream-json with -p
                "--allowedTools", ",".join(tools),
            ]
        else:
            # Execução direta via CLI
            cmd = [
                "claude",
                "-p", prompt,
                "--output-format", "stream-json",
                "--verbose",  # Required when using stream-json with -p
                "--allowedTools", ",".join(tools),
            ]

        # Continua sessão existente
        if session_id:
            cmd.extend(["--resume", session_id])

        print(f"[ClaudeBridge] Comando: {' '.join(cmd[:6])}...")

        try:
            # Define working directory
            if self.use_docker:
                # Docker: diretório dentro do container
                cwd = None  # Docker exec já define o contexto
            else:
                # CLI direto: usa diretório atual
                cwd = None

            # Executa comando
            logger.info(f"[ClaudeBridge] Iniciando processo...")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            logger.info(f"[ClaudeBridge] Processo iniciado PID={process.pid}")

            # Processa stream de saída
            line_count = 0
            if process.stdout:
                async for line in process.stdout:
                    line_str = line.decode("utf-8").strip()
                    if line_str:
                        line_count += 1
                        logger.debug(f"[ClaudeBridge] Linha {line_count}: {line_str[:100]}...")
                        # Processa linha e extrai métricas
                        data = self.token_tracker.process_stream_line(line_str)
                        if data:
                            # Sanitiza output antes de enviar
                            sanitized = Guardrail.sanitize_output(data)
                            logger.debug(f"[ClaudeBridge] Yield data type={data.get('type')}")
                            yield sanitized

            # Captura stderr para debug
            stderr_output = ""
            if process.stderr:
                stderr_output = (await process.stderr.read()).decode("utf-8")
                if stderr_output:
                    logger.warning(f"[ClaudeBridge] stderr: {stderr_output[:500]}")

            # Aguarda processo finalizar
            return_code = await process.wait()
            logger.info(f"[ClaudeBridge] Processo finalizado. return_code={return_code}, lines={line_count}")

            # Emite evento de fim com resumo de uso
            yield {
                "type": "session_end",
                "usage_summary": self.token_tracker.get_summary(),
            }

        except FileNotFoundError:
            if self.use_docker:
                yield {
                    "type": "error",
                    "error": "Docker não disponível ou container não encontrado",
                }
            else:
                yield {
                    "type": "error",
                    "error": "Claude Code CLI não encontrado. Instale com: npm install -g @anthropic-ai/claude-code",
                }
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
            }

    async def execute_simple(
        self,
        prompt: str,
        project_id: str,
        context: str = "analysis",
    ) -> Dict[str, Any]:
        """
        Executa comando e retorna resultado completo (não streaming).

        Útil para operações simples que não precisam de streaming.

        Args:
            prompt: Prompt a ser enviado
            project_id: ID do projeto
            context: Contexto da operação

        Returns:
            Dicionário com resultado e métricas
        """
        result_parts = []
        final_data = {}

        async for data in self.execute(prompt, project_id, context=context):
            if data.get("type") == "assistant":
                content = data.get("message", {}).get("content", "")
                if content:
                    result_parts.append(content)
            elif data.get("type") == "session_end":
                final_data = data

        return {
            "result": "".join(result_parts),
            "usage": final_data.get("usage_summary", {}),
        }

    def get_tracker(self) -> TokenTracker:
        """Retorna o token tracker."""
        return self.token_tracker


class ClaudeBridgeFactory:
    """Factory para criar instâncias de ClaudeBridge."""

    _instances: Dict[str, ClaudeBridge] = {}

    @classmethod
    def get_or_create(cls, tenant_id: str) -> ClaudeBridge:
        """
        Obtém ou cria um ClaudeBridge para o tenant.

        Args:
            tenant_id: ID do tenant

        Returns:
            Instância de ClaudeBridge
        """
        if tenant_id not in cls._instances:
            cls._instances[tenant_id] = ClaudeBridge(tenant_id)
        return cls._instances[tenant_id]

    @classmethod
    def remove(cls, tenant_id: str) -> None:
        """Remove instância do tenant."""
        cls._instances.pop(tenant_id, None)
