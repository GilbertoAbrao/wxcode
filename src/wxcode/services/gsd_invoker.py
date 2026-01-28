"""
GSD Invoker - Invoca Claude Code CLI para executar workflow GSD.

Este módulo é responsável por:
1. Verificar disponibilidade do Claude Code CLI
2. Invocar o workflow GSD com o arquivo CONTEXT.md
3. Fornecer feedback sobre o processo
4. Streaming de output via WebSocket
5. Processar mensagens via n8n ChatAgent workflow
"""

import asyncio
import os
import signal
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

import httpx
from rich.console import Console

from wxcode.services.bidirectional_pty import BidirectionalPTY

if TYPE_CHECKING:
    from fastapi import WebSocket

console = Console()

# n8n ChatAgent webhook URL (v2 uses HTTP Request direct to OpenAI API)
N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "https://botfy-ai-agency-n8n.tb0oe2.easypanel.host/webhook/chat-agent-v2"
)


async def _send_fallback_chat(json_data: dict, websocket: "WebSocket"):
    """
    Fallback quando n8n não está disponível.
    Extrai texto da mensagem JSON e envia como info.
    """
    try:
        msg_type = json_data.get("type", "")
        content = None

        # Tentar extrair texto de mensagem assistant
        if msg_type == "assistant":
            message_content = json_data.get("message", {}).get("content", [])
            texts = []
            for block in message_content:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text", ""))
            content = "\n".join(texts) if texts else None

        # Tentar extrair de result
        elif msg_type == "result":
            content = json_data.get("result", "")

        # Fallback para outros campos
        if not content:
            for key in ["text", "message", "content"]:
                val = json_data.get(key)
                if isinstance(val, str) and val:
                    content = val
                    break

        if content:
            await websocket.send_json({
                "type": "info",
                "content": content,
                "channel": "chat",
                "timestamp": datetime.utcnow().isoformat()
            })
    except Exception:
        pass


class GSDInvokerError(Exception):
    """Erro ao invocar Claude Code GSD workflow."""

    pass


class GSDInvoker:
    """
    Invoca Claude Code CLI para executar GSD workflow.
    """

    def __init__(
        self,
        context_md_path: Path,
        working_dir: Path,
        skill: str = "/wxcode:new-project",
    ):
        """
        Args:
            context_md_path: Path para o arquivo CONTEXT.md
            working_dir: Diretório de trabalho (onde rodar o comando)
            skill: Skill do Claude Code a invocar (default: /wxcode:new-project)
        """
        self.context_md_path = Path(context_md_path)
        self.working_dir = Path(working_dir)
        self.skill = skill

        if not self.context_md_path.exists():
            raise GSDInvokerError(f"CONTEXT.md not found at {self.context_md_path}")

        if not self.working_dir.exists():
            raise GSDInvokerError(f"Working directory not found: {self.working_dir}")

    @staticmethod
    def check_claude_code_available() -> bool:
        """
        Verifica se Claude Code CLI está instalado.

        Returns:
            True se disponível, False caso contrário
        """
        return shutil.which("claude") is not None

    def invoke_gsd(self, timeout: int = 600) -> subprocess.CompletedProcess:
        """
        Invoca o workflow GSD via Claude Code CLI.

        Args:
            timeout: Timeout em segundos (default: 600 = 10 minutos)

        Returns:
            CompletedProcess com resultado da execução

        Raises:
            GSDInvokerError: Se Claude Code não estiver disponível ou execução falhar
        """
        # Check if Claude Code is available
        if not self.check_claude_code_available():
            raise GSDInvokerError(
                "Claude Code CLI not found. Install it with:\n"
                "  npm install -g @anthropic-ai/claude-code\n"
                "Or via other installation methods: https://docs.anthropic.com/claude-code"
            )

        # Build command
        # Use relative path to CONTEXT.md for better UX
        relative_path = self.context_md_path.relative_to(self.working_dir)

        cmd = [
            "claude",
            "-p",  # Print mode (non-interactive)
            f"{self.skill} {relative_path}",
        ]

        console.print(f"[cyan]Running in {self.working_dir}: {' '.join(cmd)}[/]")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,  # Working directory set here
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True,
            )

            console.print("[green]✓ GSD workflow completed successfully[/]")
            return result

        except subprocess.TimeoutExpired:
            raise GSDInvokerError(f"GSD workflow timed out after {timeout}s")

        except subprocess.CalledProcessError as e:
            error_msg = f"GSD workflow failed with exit code {e.returncode}"
            if e.stderr:
                error_msg += f"\n\nError output:\n{e.stderr}"
            raise GSDInvokerError(error_msg)

        except Exception as e:
            raise GSDInvokerError(f"Unexpected error invoking GSD: {e}")

    def invoke_async(self) -> subprocess.Popen:
        """
        Invoca o workflow GSD de forma assíncrona (fire-and-forget).

        Returns:
            Popen process object

        Raises:
            GSDInvokerError: Se Claude Code não estiver disponível
        """
        if not self.check_claude_code_available():
            raise GSDInvokerError(
                "Claude Code CLI not found. Install it with:\n"
                "  npm install -g @anthropic-ai/claude-code"
            )

        relative_path = self.context_md_path.relative_to(self.working_dir)

        cmd = [
            "claude",
            "-p",  # Print mode (non-interactive)
            f"{self.skill} {relative_path}",
        ]

        console.print(f"[cyan]Starting async in {self.working_dir}: {' '.join(cmd)}[/]")

        process = subprocess.Popen(
            cmd, cwd=self.working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        console.print(f"[green]✓ GSD workflow started (PID: {process.pid})[/]")
        return process

    def get_command_string(self) -> str:
        """
        Retorna o comando como string para execução manual.

        Returns:
            Comando formatado para copiar/colar
        """
        relative_path = self.context_md_path.relative_to(self.working_dir)
        return f"cd {self.working_dir} && claude -p '{self.skill} {relative_path}'"

    async def invoke_with_streaming(
        self,
        websocket: "WebSocket",
        conversion_id: str,
        timeout: int = 1800,
        on_process_start: Optional[Callable[[asyncio.subprocess.Process], None]] = None,
        on_process_end: Optional[Callable[[], None]] = None,
        resize_queue: Optional[asyncio.Queue] = None,
        signal_queue: Optional[asyncio.Queue] = None,
    ) -> int:
        """
        Invoca GSD workflow com streaming de output via WebSocket.

        Args:
            websocket: WebSocket connection para streaming
            conversion_id: ID da conversão (para logging)
            timeout: Timeout em segundos (default: 1800 = 30 minutos)
            on_process_start: Callback chamado quando processo inicia (para tracking)
            on_process_end: Callback chamado quando processo termina
            resize_queue: Queue para eventos de resize (rows, cols tuples)
            signal_queue: Queue para sinais a enviar ao processo

        Returns:
            Exit code do processo
        """
        if not self.check_claude_code_available():
            raise GSDInvokerError(
                "Claude Code CLI not found. Install it with:\n"
                "  npm install -g @anthropic-ai/claude-code"
            )

        relative_path = self.context_md_path.relative_to(self.working_dir)

        # Use -p for non-interactive print mode with the prompt
        # --output-format stream-json for realtime streaming
        # --allowedTools pre-authorizes tools to avoid permission prompts
        cmd = [
            "claude",
            "-p",  # Print mode (non-interactive)
            f"{self.skill} {relative_path}",
            "--output-format", "stream-json",  # Stream JSON lines for real-time output
            "--verbose",  # Required when using stream-json with -p
            "--dangerously-skip-permissions",  # Skip ALL permission prompts in headless mode
            "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep,Task,TodoWrite",
        ]

        console.print(f"[cyan]Running (streaming) in {self.working_dir}: {' '.join(cmd)}[/]")

        import select

        # Environment variables
        env = os.environ.copy()
        env["NO_COLOR"] = "1"
        env["FORCE_COLOR"] = "0"
        env["TERM"] = "dumb"  # Simple terminal to avoid escape sequences
        # Remove API keys to prevent Claude Code CLI from using them
        # (CLI should use its own subscription login, not our API key)
        env.pop("ANTHROPIC_API_KEY", None)
        env.pop("WXCODE_LLM_KEY", None)

        # Use BidirectionalPTY for PTY management
        pty_process = BidirectionalPTY(
            cmd=cmd,
            cwd=str(self.working_dir),
            env=env,
            rows=24,
            cols=80,
        )
        await pty_process.start()

        # Notify caller about process start (for tracking/cancellation)
        if on_process_start:
            on_process_start(pty_process)

        # Usar httpx para chamar n8n ChatAgent webhook
        # Timeout alto porque n8n + OpenAI pode demorar
        http_client = httpx.AsyncClient(timeout=30.0)

        async def send_log(level: str, message: str):
            """Helper para enviar log via WebSocket."""
            try:
                await websocket.send_json({
                    "type": "log",
                    "level": level,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception:
                pass

        async def send_file_event(action: str, file_path: str):
            """Helper para enviar evento de arquivo via WebSocket."""
            try:
                await websocket.send_json({
                    "type": "file",
                    "action": action,  # "created", "modified", "read"
                    "path": file_path,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception:
                pass

        def extract_file_events(data: dict) -> list[tuple[str, str]]:
            """Extrai eventos de arquivo (Write/Edit) de uma mensagem JSON."""
            events = []
            msg_type = data.get("type", "")

            if msg_type == "assistant":
                content = data.get("message", {}).get("content", [])
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_name = block.get("name", "")
                        tool_input = block.get("input", {})
                        if tool_name == "Write":
                            path = tool_input.get("file_path", "")
                            if path:
                                events.append(("created", path))
                        elif tool_name == "Edit":
                            path = tool_input.get("file_path", "")
                            if path:
                                events.append(("modified", path))
            return events

        async def send_chat(json_data: dict):
            """Helper para enviar mensagem processada via n8n ChatAgent para o chat."""
            try:
                # Chamar n8n webhook para processar mensagem
                response = await http_client.post(N8N_WEBHOOK_URL, json=json_data)

                # Debug: logar resposta
                console.print(f"[dim]n8n response: status={response.status_code}, body={response.text[:200] if response.text else '(empty)'}[/]")

                # Verificar se resposta é válida
                if response.status_code != 200:
                    console.print(f"[yellow]n8n returned status {response.status_code}[/]")
                    return

                # Verificar se há conteúdo antes de parsear JSON
                if not response.text or not response.text.strip():
                    console.print("[yellow]n8n returned empty response, skipping[/]")
                    return

                processed = response.json()

                # Filtrar tipos que não devem ser exibidos
                msg_type = processed.get("type")
                if msg_type not in ("thinking", "blocked"):
                    ws_msg = {
                        "type": msg_type,
                        "content": processed.get("content", ""),
                        "options": processed.get("options"),
                        "confidence": processed.get("confidence"),
                        "channel": "chat",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket.send_json(ws_msg)
            except httpx.HTTPError as e:
                error_msg = f"n8n ChatAgent HTTP error: {type(e).__name__}: {e}"
                console.print(f"[red]ERROR: {error_msg}[/]")
                console.print(f"[red]URL: {N8N_WEBHOOK_URL}[/]")
                # Notificar frontend sobre problema de conexão
                await websocket.send_json({
                    "type": "error",
                    "content": f"⚠️ Problema de conexão com o agente de chat. Erro: {type(e).__name__}",
                    "channel": "chat",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                import traceback
                error_msg = f"n8n processing error: {type(e).__name__}: {e}"
                console.print(f"[red]ERROR: {error_msg}[/]")
                console.print(f"[red]{traceback.format_exc()}[/]")
                # Notificar frontend sobre problema de conexão
                await websocket.send_json({
                    "type": "error",
                    "content": f"⚠️ Erro ao processar mensagem do agente: {type(e).__name__}",
                    "channel": "chat",
                    "timestamp": datetime.utcnow().isoformat()
                })

        def extract_text_from_json(data: dict) -> str | None:
            """Extrai texto de uma mensagem JSON do stream-json."""
            msg_type = data.get("type", "")

            # Se for mensagem de assistente, extrair blocos de texto
            if msg_type == "assistant":
                content = data.get("message", {}).get("content", [])
                texts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            texts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "unknown")
                            tool_input = block.get("input", {})
                            # Format tool call with input
                            if tool_name == "Bash":
                                cmd = tool_input.get("command", "")
                                desc = tool_input.get("description", "")
                                # Use description for complex commands, truncate long ones
                                if desc and len(cmd) > 80:
                                    texts.append(f"$ {desc}")
                                elif len(cmd) > 120:
                                    texts.append(f"$ {cmd[:120]}...")
                                else:
                                    texts.append(f"$ {cmd}")
                            elif tool_name == "Read":
                                path = tool_input.get("file_path", "")
                                texts.append(f"[reading: {path}]")
                            elif tool_name == "Write":
                                path = tool_input.get("file_path", "")
                                texts.append(f"[writing: {path}]")
                            elif tool_name == "Edit":
                                path = tool_input.get("file_path", "")
                                texts.append(f"[editing: {path}]")
                            elif tool_name in ("Glob", "Grep"):
                                pattern = tool_input.get("pattern", "")
                                texts.append(f"[{tool_name.lower()}: {pattern}]")
                            elif tool_name == "Task":
                                desc = tool_input.get("description", "")
                                texts.append(f"[task: {desc}]")
                            else:
                                texts.append(f"[{tool_name}]")
                return "\n".join(texts) if texts else None

            # Se for resultado de tool (user message com tool_result)
            if msg_type == "user":
                content = data.get("message", {}).get("content", [])
                texts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "tool_result":
                            result_content = block.get("content", "")
                            # Truncate long results
                            if isinstance(result_content, str):
                                if len(result_content) > 500:
                                    result_content = result_content[:500] + "... [truncated]"
                                texts.append(result_content)
                            elif isinstance(result_content, list):
                                # Handle array of content blocks
                                for item in result_content:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        text = item.get("text", "")
                                        if len(text) > 500:
                                            text = text[:500] + "... [truncated]"
                                        texts.append(text)
                return "\n".join(texts) if texts else None

            # Se for resultado final
            if msg_type == "result":
                result = data.get("result", "")
                if result:
                    return f"[result] {result}"
                return None

            # Se for mensagem de sistema
            if msg_type == "system":
                return data.get("message", data.get("text", ""))

            # Fallback: tentar extrair qualquer campo de texto
            for key in ["text", "message", "content", "result"]:
                val = data.get(key)
                if isinstance(val, str) and val:
                    return val

            return None

        async def stream_pty_output():
            """Stream output from PTY master fd to WebSocket (supports stream-json)."""
            import json as json_module
            import re

            # Pattern to match ANSI escape sequences and control characters
            ansi_pattern = re.compile(r'''
                \x1b\[[0-9;]*[a-zA-Z]|  # Standard ANSI escape sequences
                \x1b\][^\x07]*\x07|     # OSC sequences
                \x1b\[\?[0-9;]*[a-zA-Z]|  # Private mode sequences (e.g., ?1004l)
                [\x00-\x08\x0b\x0c\x0e-\x1f]|  # Control characters (except \t, \n, \r)
                \r                      # Carriage returns from PTY
            ''', re.VERBOSE)

            def clean_text(text: str) -> str:
                """Remove ANSI escape sequences and control characters."""
                return ansi_pattern.sub('', text).strip()

            async def process_line(text: str, line_count: int):
                """Process a single line of output."""
                console.print(f"[green]DEBUG line {line_count}: {text[:150]}...[/]" if len(text) > 150 else f"[green]DEBUG line {line_count}: {text}[/]")

                # Tentar parsear como JSON (stream-json format)
                try:
                    data = json_module.loads(text)
                    # Enviar para terminal (log)
                    extracted = extract_text_from_json(data)
                    if extracted:
                        await send_log("info", extracted)
                    # Enviar eventos de arquivo (Write/Edit)
                    file_events = extract_file_events(data)
                    for action, path in file_events:
                        await send_file_event(action, path)
                    # Enviar para chat (processado pelo n8n ChatAgent)
                    await send_chat(data)
                except json_module.JSONDecodeError:
                    # Não é JSON, enviar como texto puro
                    await send_log("info", text)

            console.print(f"[yellow]DEBUG: stream_pty_output started, fd={pty_process.master_fd}[/]")
            line_count = 0
            buffer = ""
            loop = asyncio.get_event_loop()

            try:
                while True:
                    # Check if process is still running
                    if pty_process.returncode is not None:
                        console.print(f"[yellow]DEBUG: process exited, draining buffer[/]")
                        # Process remaining buffer
                        if buffer:
                            for line in buffer.split('\n'):
                                line = clean_text(line)
                                if line:
                                    line_count += 1
                                    await process_line(line, line_count)
                        break

                    # Read from PTY master fd (non-blocking via executor)
                    try:
                        # Use select to check if data is available
                        readable, _, _ = await loop.run_in_executor(
                            None, lambda: select.select([pty_process.master_fd], [], [], 0.1)
                        )
                        if not readable:
                            continue

                        data = await pty_process.read(4096)
                        if not data:
                            console.print(f"[yellow]DEBUG: PTY EOF after {line_count} lines[/]")
                            break

                        buffer += data.decode("utf-8", errors="replace")

                        # Process complete lines
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = clean_text(line)
                            if not line:
                                continue
                            line_count += 1
                            await process_line(line, line_count)

                    except OSError as e:
                        # PTY closed
                        console.print(f"[yellow]DEBUG: PTY closed: {e}[/]")
                        break

            finally:
                # Note: master_fd is closed by pty_process.close()
                pass

            console.print(f"[yellow]DEBUG: stream_pty_output finished, {line_count} lines[/]")

        async def handle_resize():
            """Handle resize events from queue."""
            if resize_queue is None:
                return
            while not pty_process._closed:
                try:
                    rows, cols = await asyncio.wait_for(resize_queue.get(), timeout=0.5)
                    await pty_process.resize(rows, cols)
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break

        async def handle_signals():
            """Handle signal events from queue."""
            if signal_queue is None:
                return
            while not pty_process._closed:
                try:
                    sig = await asyncio.wait_for(signal_queue.get(), timeout=0.5)
                    await pty_process.send_signal(sig)
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break

        try:
            # Create tasks for concurrent execution
            tasks = [asyncio.create_task(stream_pty_output())]
            if resize_queue:
                tasks.append(asyncio.create_task(handle_resize()))
            if signal_queue:
                tasks.append(asyncio.create_task(handle_signals()))

            # Wait with timeout - when output streaming completes, cancel others
            done, pending = await asyncio.wait(
                tasks,
                timeout=timeout,
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Check if we completed or timed out
            if not done:
                # All tasks timed out
                raise asyncio.TimeoutError()

            return_code = pty_process.returncode if pty_process.returncode is not None else 0

        except asyncio.TimeoutError:
            await pty_process.send_signal(signal.SIGKILL)
            await send_log("error", f"Processo interrompido por timeout ({timeout}s)")
            return_code = -1

        except Exception as e:
            await pty_process.send_signal(signal.SIGKILL)
            await send_log("error", f"Erro inesperado: {e}")
            console.print(f"[red]Exception: {e}[/]")
            import traceback
            traceback.print_exc()
            return_code = -1

        finally:
            # Cleanup PTY (closes master_fd and terminates process)
            await pty_process.close()
            # Cleanup httpx client
            await http_client.aclose()
            # Notify caller that process ended
            if on_process_end:
                on_process_end()

        if return_code == 0:
            console.print("[green]✓ GSD workflow completed successfully (streaming)[/]")
        else:
            console.print(f"[red]✗ GSD workflow failed with code {return_code}[/]")

        return return_code

    async def resume_with_streaming(
        self,
        websocket: "WebSocket",
        conversion_id: str,
        user_message: Optional[str] = None,
        timeout: int = 1800,
        on_process_start: Optional[Callable[[asyncio.subprocess.Process], None]] = None,
        on_process_end: Optional[Callable[[], None]] = None,
        resize_queue: Optional[asyncio.Queue] = None,
        signal_queue: Optional[asyncio.Queue] = None,
    ) -> int:
        """
        Retoma conversa Claude Code existente com streaming de output via WebSocket.

        Usa `claude --continue` para continuar a conversa no working_dir.

        Args:
            websocket: WebSocket connection para streaming
            conversion_id: ID da conversão (para logging)
            user_message: Mensagem do usuário para enviar (se fornecida, usa como prompt)
            timeout: Timeout em segundos (default: 1800 = 30 minutos)
            on_process_start: Callback chamado quando processo inicia (para tracking)
            on_process_end: Callback chamado quando processo termina
            resize_queue: Queue para eventos de resize (rows, cols tuples)
            signal_queue: Queue para sinais a enviar ao processo

        Returns:
            Exit code do processo
        """
        if not self.check_claude_code_available():
            raise GSDInvokerError(
                "Claude Code CLI not found. Install it with:\n"
                "  npm install -g @anthropic-ai/claude-code"
            )

        # Use --continue to continue the most recent conversation in this directory
        # Combined with -p for headless mode
        # --output-format stream-json for real-time streaming

        # Use user_message if provided, otherwise use default continuation prompt
        prompt = user_message if user_message else \
            "Continue de onde parou. Se estava aguardando resposta, prossiga com a opção mais adequada."

        cmd = [
            "claude",
            "-p",  # Print mode (non-interactive)
            prompt,
            "--continue",  # Continue most recent conversation in this directory
            "--output-format", "stream-json",  # Stream JSON lines for real-time output
            "--verbose",  # Required when using stream-json with -p
            "--dangerously-skip-permissions",  # Skip ALL permission prompts in headless mode
            "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep,Task,TodoWrite",
        ]

        console.print(f"[cyan]Resuming in {self.working_dir}: {' '.join(cmd)}[/]")

        import select

        # Environment variables
        env = os.environ.copy()
        env["NO_COLOR"] = "1"
        env["FORCE_COLOR"] = "0"
        env["TERM"] = "dumb"  # Simple terminal to avoid escape sequences
        # Remove API keys to prevent Claude Code CLI from using them
        # (CLI should use its own subscription login, not our API key)
        env.pop("ANTHROPIC_API_KEY", None)
        env.pop("WXCODE_LLM_KEY", None)

        # Use BidirectionalPTY for PTY management
        pty_process = BidirectionalPTY(
            cmd=cmd,
            cwd=str(self.working_dir),
            env=env,
            rows=24,
            cols=80,
        )
        await pty_process.start()

        # Notify caller about process start (for tracking/cancellation)
        if on_process_start:
            on_process_start(pty_process)

        # Usar httpx para chamar n8n ChatAgent webhook
        # Timeout alto porque n8n + OpenAI pode demorar
        http_client = httpx.AsyncClient(timeout=30.0)

        async def send_log(level: str, message: str):
            """Helper para enviar log via WebSocket."""
            try:
                await websocket.send_json({
                    "type": "log",
                    "level": level,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception:
                pass

        async def send_file_event(action: str, file_path: str):
            """Helper para enviar evento de arquivo via WebSocket."""
            try:
                await websocket.send_json({
                    "type": "file",
                    "action": action,  # "created", "modified", "read"
                    "path": file_path,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception:
                pass

        def extract_file_events(data: dict) -> list[tuple[str, str]]:
            """Extrai eventos de arquivo (Write/Edit) de uma mensagem JSON."""
            events = []
            msg_type = data.get("type", "")

            if msg_type == "assistant":
                content = data.get("message", {}).get("content", [])
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_name = block.get("name", "")
                        tool_input = block.get("input", {})
                        if tool_name == "Write":
                            path = tool_input.get("file_path", "")
                            if path:
                                events.append(("created", path))
                        elif tool_name == "Edit":
                            path = tool_input.get("file_path", "")
                            if path:
                                events.append(("modified", path))
            return events

        async def send_chat(json_data: dict):
            """Helper para enviar mensagem processada via n8n ChatAgent para o chat."""
            try:
                # Chamar n8n webhook para processar mensagem
                response = await http_client.post(N8N_WEBHOOK_URL, json=json_data)

                # Debug: logar resposta
                console.print(f"[dim]n8n response: status={response.status_code}, body={response.text[:200] if response.text else '(empty)'}[/]")

                # Verificar se resposta é válida
                if response.status_code != 200:
                    console.print(f"[yellow]n8n returned status {response.status_code}[/]")
                    return

                # Verificar se há conteúdo antes de parsear JSON
                if not response.text or not response.text.strip():
                    console.print("[yellow]n8n returned empty response, skipping[/]")
                    return

                processed = response.json()

                # Filtrar tipos que não devem ser exibidos
                msg_type = processed.get("type")
                if msg_type not in ("thinking", "blocked"):
                    ws_msg = {
                        "type": msg_type,
                        "content": processed.get("content", ""),
                        "options": processed.get("options"),
                        "confidence": processed.get("confidence"),
                        "channel": "chat",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket.send_json(ws_msg)
            except httpx.HTTPError as e:
                error_msg = f"n8n ChatAgent HTTP error: {type(e).__name__}: {e}"
                console.print(f"[red]ERROR: {error_msg}[/]")
                console.print(f"[red]URL: {N8N_WEBHOOK_URL}[/]")
                # Notificar frontend sobre problema de conexão
                await websocket.send_json({
                    "type": "error",
                    "content": f"⚠️ Problema de conexão com o agente de chat. Erro: {type(e).__name__}",
                    "channel": "chat",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                import traceback
                error_msg = f"n8n processing error: {type(e).__name__}: {e}"
                console.print(f"[red]ERROR: {error_msg}[/]")
                console.print(f"[red]{traceback.format_exc()}[/]")
                # Notificar frontend sobre problema de conexão
                await websocket.send_json({
                    "type": "error",
                    "content": f"⚠️ Erro ao processar mensagem do agente: {type(e).__name__}",
                    "channel": "chat",
                    "timestamp": datetime.utcnow().isoformat()
                })

        def extract_text_from_json(data: dict) -> str | None:
            """Extrai texto de uma mensagem JSON do stream-json."""
            msg_type = data.get("type", "")

            # Se for mensagem de assistente, extrair blocos de texto
            if msg_type == "assistant":
                content = data.get("message", {}).get("content", [])
                texts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            texts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "unknown")
                            tool_input = block.get("input", {})
                            # Format tool call with input
                            if tool_name == "Bash":
                                cmd = tool_input.get("command", "")
                                desc = tool_input.get("description", "")
                                # Use description for complex commands, truncate long ones
                                if desc and len(cmd) > 80:
                                    texts.append(f"$ {desc}")
                                elif len(cmd) > 120:
                                    texts.append(f"$ {cmd[:120]}...")
                                else:
                                    texts.append(f"$ {cmd}")
                            elif tool_name == "Read":
                                path = tool_input.get("file_path", "")
                                texts.append(f"[reading: {path}]")
                            elif tool_name == "Write":
                                path = tool_input.get("file_path", "")
                                texts.append(f"[writing: {path}]")
                            elif tool_name == "Edit":
                                path = tool_input.get("file_path", "")
                                texts.append(f"[editing: {path}]")
                            elif tool_name in ("Glob", "Grep"):
                                pattern = tool_input.get("pattern", "")
                                texts.append(f"[{tool_name.lower()}: {pattern}]")
                            elif tool_name == "Task":
                                desc = tool_input.get("description", "")
                                texts.append(f"[task: {desc}]")
                            else:
                                texts.append(f"[{tool_name}]")
                return "\n".join(texts) if texts else None

            # Se for resultado de tool (user message com tool_result)
            if msg_type == "user":
                content = data.get("message", {}).get("content", [])
                texts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "tool_result":
                            result_content = block.get("content", "")
                            # Truncate long results
                            if isinstance(result_content, str):
                                if len(result_content) > 500:
                                    result_content = result_content[:500] + "... [truncated]"
                                texts.append(result_content)
                            elif isinstance(result_content, list):
                                # Handle array of content blocks
                                for item in result_content:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        text = item.get("text", "")
                                        if len(text) > 500:
                                            text = text[:500] + "... [truncated]"
                                        texts.append(text)
                return "\n".join(texts) if texts else None

            # Se for resultado final
            if msg_type == "result":
                result = data.get("result", "")
                if result:
                    return f"[result] {result}"
                return None

            # Se for mensagem de sistema
            if msg_type == "system":
                return data.get("message", data.get("text", ""))

            # Fallback: tentar extrair qualquer campo de texto
            for key in ["text", "message", "content", "result"]:
                val = data.get(key)
                if isinstance(val, str) and val:
                    return val

            return None

        async def stream_pty_output():
            """Stream output from PTY master fd to WebSocket (supports stream-json)."""
            import json as json_module
            import re

            # Pattern to match ANSI escape sequences and control characters
            ansi_pattern = re.compile(r'''
                \x1b\[[0-9;]*[a-zA-Z]|  # Standard ANSI escape sequences
                \x1b\][^\x07]*\x07|     # OSC sequences
                \x1b\[\?[0-9;]*[a-zA-Z]|  # Private mode sequences (e.g., ?1004l)
                [\x00-\x08\x0b\x0c\x0e-\x1f]|  # Control characters (except \t, \n, \r)
                \r                      # Carriage returns from PTY
            ''', re.VERBOSE)

            def clean_text(text: str) -> str:
                """Remove ANSI escape sequences and control characters."""
                return ansi_pattern.sub('', text).strip()

            async def process_line(text: str, line_count: int):
                """Process a single line of output."""
                console.print(f"[green]DEBUG line {line_count}: {text[:150]}...[/]" if len(text) > 150 else f"[green]DEBUG line {line_count}: {text}[/]")

                # Tentar parsear como JSON (stream-json format)
                try:
                    data = json_module.loads(text)
                    # Enviar para terminal (log)
                    extracted = extract_text_from_json(data)
                    if extracted:
                        await send_log("info", extracted)
                    # Enviar eventos de arquivo (Write/Edit)
                    file_events = extract_file_events(data)
                    for action, path in file_events:
                        await send_file_event(action, path)
                    # Enviar para chat (processado pelo n8n ChatAgent)
                    await send_chat(data)
                except json_module.JSONDecodeError:
                    # Não é JSON, enviar como texto puro
                    await send_log("info", text)

            console.print(f"[yellow]DEBUG: stream_pty_output started, fd={pty_process.master_fd}[/]")
            line_count = 0
            buffer = ""
            loop = asyncio.get_event_loop()

            try:
                while True:
                    # Check if process is still running
                    if pty_process.returncode is not None:
                        console.print(f"[yellow]DEBUG: process exited, draining buffer[/]")
                        # Process remaining buffer
                        if buffer:
                            for line in buffer.split('\n'):
                                line = clean_text(line)
                                if line:
                                    line_count += 1
                                    await process_line(line, line_count)
                        break

                    # Read from PTY master fd (non-blocking via executor)
                    try:
                        # Use select to check if data is available
                        readable, _, _ = await loop.run_in_executor(
                            None, lambda: select.select([pty_process.master_fd], [], [], 0.1)
                        )
                        if not readable:
                            continue

                        data = await pty_process.read(4096)
                        if not data:
                            console.print(f"[yellow]DEBUG: PTY EOF after {line_count} lines[/]")
                            break

                        buffer += data.decode("utf-8", errors="replace")

                        # Process complete lines
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = clean_text(line)
                            if not line:
                                continue
                            line_count += 1
                            await process_line(line, line_count)

                    except OSError as e:
                        # PTY closed
                        console.print(f"[yellow]DEBUG: PTY closed: {e}[/]")
                        break

            finally:
                # Note: master_fd is closed by pty_process.close()
                pass

            console.print(f"[yellow]DEBUG: stream_pty_output finished, {line_count} lines[/]")

        async def handle_resize():
            """Handle resize events from queue."""
            if resize_queue is None:
                return
            while not pty_process._closed:
                try:
                    rows, cols = await asyncio.wait_for(resize_queue.get(), timeout=0.5)
                    await pty_process.resize(rows, cols)
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break

        async def handle_signals():
            """Handle signal events from queue."""
            if signal_queue is None:
                return
            while not pty_process._closed:
                try:
                    sig = await asyncio.wait_for(signal_queue.get(), timeout=0.5)
                    await pty_process.send_signal(sig)
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break

        try:
            # Create tasks for concurrent execution
            tasks = [asyncio.create_task(stream_pty_output())]
            if resize_queue:
                tasks.append(asyncio.create_task(handle_resize()))
            if signal_queue:
                tasks.append(asyncio.create_task(handle_signals()))

            # Wait with timeout - when output streaming completes, cancel others
            done, pending = await asyncio.wait(
                tasks,
                timeout=timeout,
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Check if we completed or timed out
            if not done:
                # All tasks timed out
                raise asyncio.TimeoutError()

            return_code = pty_process.returncode if pty_process.returncode is not None else 0

        except asyncio.TimeoutError:
            await pty_process.send_signal(signal.SIGKILL)
            await send_log("error", f"Processo interrompido por timeout ({timeout}s)")
            return_code = -1

        except Exception as e:
            await pty_process.send_signal(signal.SIGKILL)
            await send_log("error", f"Erro inesperado: {e}")
            console.print(f"[red]Exception: {e}[/]")
            import traceback
            traceback.print_exc()
            return_code = -1

        finally:
            # Cleanup PTY (closes master_fd and terminates process)
            await pty_process.close()
            # Cleanup httpx client
            await http_client.aclose()
            # Notify caller that process ended
            if on_process_end:
                on_process_end()

        if return_code == 0:
            console.print("[green]✓ GSD resume completed successfully (streaming)[/]")
        else:
            console.print(f"[red]✗ GSD resume failed with code {return_code}[/]")

        return return_code
