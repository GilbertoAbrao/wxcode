"""
Executor de etapas do wizard de importação.
"""

import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from wxcode.models.import_session import ImportSession, StepResult


class StepExecutor:
    """Executa comandos CLI para cada etapa do wizard."""

    def __init__(self):
        self.active_processes: Dict[str, asyncio.subprocess.Process] = {}

    async def execute_step(
        self,
        session: ImportSession,
        step: int,
        websocket: Any,
    ) -> StepResult:
        """
        Executa uma etapa específica do wizard.

        Args:
            session: Sessão de importação
            step: Número da etapa (2-6)
            websocket: WebSocket para streaming de logs

        Returns:
            Resultado da etapa com métricas
        """
        # Mapear step para comando
        commands = self._get_commands_for_step(session, step)
        if not commands:
            raise ValueError(f"Step {step} não possui comando associado")

        # Atualizar status
        session.update_step_status(step, "running")
        await session.save()

        metrics: Dict[str, Any] = {}
        log_lines = 0
        error_message: Optional[str] = None

        try:
            for cmd_name, cmd_args in commands:
                await self._send_log(websocket, "info", f"Executando: {cmd_name}")

                # Executar comando
                process = await asyncio.create_subprocess_exec(
                    *cmd_args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                # Armazenar processo ativo
                self.active_processes[session.session_id] = process

                # Stream stdout/stderr
                async def stream_output(stream, level):
                    nonlocal log_lines, metrics
                    while True:
                        line = await stream.readline()
                        if not line:
                            break
                        text = line.decode().rstrip()
                        log_lines += 1

                        # Enviar log via WebSocket
                        await self._send_log(websocket, level, text)

                        # Tentar extrair progresso (para barra de progresso visual)
                        progress_data = self._extract_progress(text, step)
                        if progress_data:
                            await self._send_progress(websocket, step, progress_data)

                        # Tentar extrair métricas
                        extracted = self._extract_metrics(text)
                        if extracted:
                            metrics.update(extracted)
                            await self._send_metrics(websocket, step, extracted)

                # Stream ambos stdout e stderr em paralelo
                await asyncio.gather(
                    stream_output(process.stdout, "info"),
                    stream_output(process.stderr, "error"),
                )

                # Aguardar término
                return_code = await process.wait()

                # Remover processo da lista de ativos
                self.active_processes.pop(session.session_id, None)

                if return_code != 0:
                    error_message = f"Comando falhou com código {return_code}"
                    session.update_step_status(step, "failed", error_message=error_message)
                    await session.save()
                    await self._send_error(websocket, error_message)
                    break

        except Exception as e:
            error_message = str(e)
            session.update_step_status(step, "failed", error_message=error_message)
            await session.save()
            await self._send_error(websocket, error_message)

        # Atualizar status final
        if not error_message:
            session.update_step_status(step, "completed", metrics=metrics)
            await session.save()

        # Criar e retornar resultado
        step_result = session.get_step_result(step)
        if step_result:
            step_result.log_lines = log_lines
            await self._send_step_complete(websocket, step_result)

        return step_result or StepResult(
            step=step,
            name=f"step-{step}",
            status="failed",
            error_message=error_message or "Unknown error",
            log_lines=log_lines,
        )

    async def cancel_session(self, session_id: str) -> None:
        """Cancela processos em execução de uma sessão."""
        process = self.active_processes.get(session_id)
        if process and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
            self.active_processes.pop(session_id, None)

    def _get_commands_for_step(
        self, session: ImportSession, step: int
    ) -> list[tuple[str, list[str]]]:
        """Retorna lista de comandos para uma etapa."""
        project_path = session.project_path
        pdf_docs = session.pdf_docs_path

        # Extrair nome e diretório do projeto
        project_file = Path(project_path)
        original_name = project_file.stem
        project_dir = str(project_file.parent)  # Diretório do projeto (sem o .wwp)

        # Nome do projeto no banco inclui workspace_id suffix
        if session.workspace_id:
            project_name = f"{original_name}_{session.workspace_id}"
        else:
            project_name = original_name

        # Usar Python do virtualenv atual com -m para garantir imports corretos
        python = sys.executable

        # Para step 3, precisamos primeiro fazer split-pdf de cada PDF, depois enrich
        step3_commands = []
        if pdf_docs:
            # Listar todos os PDFs no diretório de upload
            pdf_dir = Path(pdf_docs)
            if pdf_dir.exists():
                pdf_files = list(pdf_dir.glob("*.pdf"))

                # Diretório de saída para os PDFs divididos
                split_output = pdf_dir / "split"

                # Adicionar comando split-pdf para cada PDF
                for pdf_file in pdf_files:
                    step3_commands.append((
                        f"wxcode split-pdf {pdf_file.name}",
                        [python, "-m", "wxcode.cli", "split-pdf", str(pdf_file),
                         "--output", str(split_output), "--project", project_name]
                    ))

                # Depois de dividir todos os PDFs, executar enrich com o diretório split
                step3_commands.append((
                    "wxcode enrich",
                    [python, "-m", "wxcode.cli", "enrich", project_dir,
                     "--pdf-docs", str(split_output), "--project", project_name]
                ))
            else:
                # Se não houver PDFs, apenas enrich sem PDFs
                step3_commands.append((
                    "wxcode enrich",
                    [python, "-m", "wxcode.cli", "enrich", project_dir,
                     "--project", project_name]
                ))
        else:
            # Sem PDFs, apenas enrich
            step3_commands.append((
                "wxcode enrich",
                [python, "-m", "wxcode.cli", "enrich", project_dir,
                 "--project", project_name]
            ))

        # Build step 2 command with workspace options
        import_cmd = [python, "-m", "wxcode.cli", "import", project_path, "--force"]

        # Add workspace options if available in session
        if session.workspace_id:
            import_cmd.extend(["--workspace-id", session.workspace_id])
        if session.workspace_path:
            import_cmd.extend(["--workspace-path", session.workspace_path])

        commands_map = {
            2: [("wxcode import", import_cmd)],
            3: step3_commands,
            4: [
                # Schema PRIMEIRO - define estrutura do banco (tabelas, colunas, tipos)
                ("wxcode parse-schema", [python, "-m", "wxcode.cli", "parse-schema", project_dir,
                 "--project", project_name]),
                # Procedures SEGUNDO - podem referenciar tabelas em queries SQL
                ("wxcode parse-procedures", [python, "-m", "wxcode.cli", "parse-procedures", project_dir,
                 "--project", project_name]),
                # Classes TERCEIRO - podem ter dependências com data files (tabelas)
                ("wxcode parse-classes", [python, "-m", "wxcode.cli", "parse-classes", project_dir,
                 "--project", project_name]),
            ],
            5: [("wxcode analyze", [python, "-m", "wxcode.cli", "analyze", project_name])],
            6: [("wxcode sync-neo4j", [python, "-m", "wxcode.cli", "sync-neo4j", project_name])],
        }

        return commands_map.get(step, [])

    def _extract_metrics(self, text: str) -> Dict[str, Any]:
        """Extrai métricas do output do CLI."""
        metrics = {}

        # Padrões comuns de output
        patterns = {
            r"Imported (\d+) elements": "elements_count",
            r"(\d+) elements imported": "elements_count",
            r"(\d+) controls extracted": "controls_count",
            r"(\d+) procedures parsed": "procedures_count",
            r"(\d+) classes parsed": "classes_count",
            r"(\d+) tables parsed": "tables_count",
            r"(\d+) dependencies found": "dependencies_count",
            r"(\d+) nodes synced": "neo4j_nodes",
            r"(\d+) relationships created": "neo4j_relationships",
        }

        for pattern, metric_name in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metrics[metric_name] = int(match.group(1))

        return metrics

    async def _send_log(self, websocket: Any, level: str, message: str) -> None:
        """Envia evento de log via WebSocket."""
        event = {
            "type": "log",
            "log": {
                "level": level,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
        await websocket.send_text(json.dumps(event))

    async def _send_metrics(
        self, websocket: Any, step: int, metrics: Dict[str, Any]
    ) -> None:
        """Envia evento de métricas via WebSocket."""
        event = {"type": "metrics", "metrics": {"step": step, "data": metrics}}
        await websocket.send_text(json.dumps(event))

    async def _send_error(self, websocket: Any, error_message: str) -> None:
        """Envia evento de erro via WebSocket."""
        event = {"type": "error", "error": {"message": error_message}}
        await websocket.send_text(json.dumps(event))

    def _extract_progress(self, text: str, step: int) -> Optional[Dict[str, Any]]:
        """
        Extrai progresso do output do CLI.

        Busca padrões como: "Processando: 10/63 (15.9%)"
        """
        # Padrão para progresso: "Processando: X/Y (Z%)"
        pattern = r"Processando:\s+(\d+)/(\d+)\s+\(([0-9.]+)%\)"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            current = int(match.group(1))
            total = int(match.group(2))
            percent = float(match.group(3))

            return {
                "current": current,
                "total": total,
                "percent": percent,
            }

        return None

    async def _send_progress(
        self, websocket: Any, step: int, progress: Dict[str, Any]
    ) -> None:
        """Envia evento de progresso via WebSocket."""
        event = {
            "type": "progress",
            "progress": {
                "step": step,
                "current": progress["current"],
                "total": progress["total"],
                "percent": progress["percent"],
            },
        }
        await websocket.send_text(json.dumps(event))

    async def _send_step_complete(self, websocket: Any, step_result: StepResult) -> None:
        """Envia evento de conclusão de etapa via WebSocket."""
        event = {
            "type": "step_complete",
            "step_result": {
                "step": step_result.step,
                "name": step_result.name,
                "status": step_result.status,
                "started_at": step_result.started_at.isoformat()
                if step_result.started_at
                else None,
                "completed_at": step_result.completed_at.isoformat()
                if step_result.completed_at
                else None,
                "metrics": step_result.metrics,
                "log_lines": step_result.log_lines,
                "error_message": step_result.error_message,
            },
        }
        await websocket.send_text(json.dumps(event))
