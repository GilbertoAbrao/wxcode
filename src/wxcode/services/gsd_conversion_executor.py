"""
Executor de conversões via comando gsd-context.

Substitui o ConversionExecutor baseado em spec-proposal por execução
do comando CLI gsd-context que coleta contexto e dispara GSD workflow.
"""

from pathlib import Path
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from wxcode.models import Element
from wxcode.llm_converter import ConversionTracker
from wxcode.services.gsd_context_collector import (
    GSDContextCollector,
    GSDContextWriter,
    create_gsd_branch,
)
from wxcode.services.gsd_invoker import GSDInvoker, GSDInvokerError


class GSDConversionResult:
    """Resultado da execução de uma conversão via GSD."""

    def __init__(
        self,
        success: bool,
        element_name: Optional[str] = None,
        element_id: Optional[str] = None,
        context_path: Optional[Path] = None,
        branch_name: Optional[str] = None,
        error: Optional[str] = None,
        skipped_count: int = 0,
    ):
        self.success = success
        self.element_name = element_name
        self.element_id = element_id
        self.context_path = context_path
        self.branch_name = branch_name
        self.error = error
        self.skipped_count = skipped_count


class GSDConversionExecutor:
    """
    Executor para conversões via comando gsd-context.

    Busca próximo elemento pendente, coleta contexto,
    cria branch git, exporta arquivos e dispara GSD workflow.
    """

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        neo4j_conn=None,
        output_base: Optional[Path] = None,
        skip_gsd: bool = False,
        no_branch: bool = False,
    ):
        """
        Inicializa o executor.

        Args:
            db: Database MongoDB
            neo4j_conn: Conexão Neo4j (opcional, usa fallback se None)
            output_base: Diretório base para output (padrão: ./output/gsd-context)
            skip_gsd: Se True, só coleta contexto sem disparar GSD
            no_branch: Se True, não cria nova branch git
        """
        self.db = db
        self.client = db.client  # Extrair client do database
        self.neo4j_conn = neo4j_conn
        self.output_base = output_base or Path("./output/gsd-context")
        self.skip_gsd = skip_gsd
        self.no_branch = no_branch
        self.tracker = ConversionTracker(db)

    async def execute_next_pending(
        self, project_name: str, max_skips: int = 100
    ) -> GSDConversionResult:
        """
        Executa conversão do próximo elemento pendente via gsd-context.

        Pula automaticamente items não suportados (classes, procedures)
        marcando-os como 'skipped' e busca o próximo válido (page).

        Args:
            project_name: Nome do projeto
            max_skips: Máximo de items a pular antes de desistir (padrão: 100)

        Returns:
            Resultado da execução
        """
        try:
            skipped_count = 0

            # Loop até encontrar um item suportado ou esgotar candidatos
            while skipped_count < max_skips:
                # Buscar próximo item pendente
                item = await self.tracker.get_next_pending_item(project_name)

                if not item:
                    if skipped_count > 0:
                        return GSDConversionResult(
                            success=False,
                            error=f"Nenhum elemento suportado encontrado (pulados: {skipped_count} classes/procedures)",
                            skipped_count=skipped_count,
                        )
                    return GSDConversionResult(
                        success=False,
                        error="Nenhum elemento pendente encontrado",
                        skipped_count=0,
                    )

                # Por enquanto só suporta pages (elements collection)
                if item.collection != "elements":
                    # Marcar como skipped e buscar próximo
                    await self._mark_item_skipped(item)
                    skipped_count += 1
                    continue

                # Encontrou elemento suportado, executar via gsd-context
                return await self.execute_element(
                    item.name, project_name, skipped_count
                )

            # Excedeu limite de skips
            return GSDConversionResult(
                success=False,
                error=f"Excedido limite de {max_skips} items não suportados para pular",
                skipped_count=skipped_count,
            )

        except Exception as e:
            import traceback
            return GSDConversionResult(
                success=False,
                error=f"Erro ao executar conversão: {str(e)}\n{traceback.format_exc()}",
            )

    async def execute_element(
        self,
        element_name: str,
        project_name: Optional[str] = None,
        skipped_count: int = 0,
    ) -> GSDConversionResult:
        """
        Executa conversão de um elemento específico via gsd-context.

        Args:
            element_name: Nome do elemento
            project_name: Nome do projeto (opcional, para auto-detect)
            skipped_count: Número de items que foram pulados antes deste

        Returns:
            Resultado da execução
        """
        try:
            # 1. Criar branch git (se não --no-branch)
            if not self.no_branch:
                branch_name = create_gsd_branch(element_name, self.no_branch)
            else:
                import subprocess
                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                branch_name = result.stdout.strip()

            # 2. Coletar dados do elemento
            collector = GSDContextCollector(self.client, self.neo4j_conn)
            data = await collector.collect(
                element_name=element_name,
                project_name=project_name,
                depth=2,
            )

            # 3. Determinar output dir
            output_dir = self.output_base / element_name

            # 4. Escrever arquivos
            writer = GSDContextWriter(output_dir)
            files = writer.write_all(data, branch_name)

            # 5. Atualizar status do elemento para 'in_progress'
            from wxcode.models.element import ConversionStatus
            element = data.element
            await self.tracker.mark_status(str(element.id), ConversionStatus.IN_PROGRESS)

            # 6. Disparar GSD workflow (se não --skip-gsd)
            if not self.skip_gsd:
                try:
                    invoker = GSDInvoker(
                        context_md_path=files["context"],
                        working_dir=output_dir,
                    )
                    # Usar invoke_async() para não travar o backend
                    process = invoker.invoke_async()

                    # Retorna sucesso imediatamente (processo roda em background)
                    # O usuário pode monitorar o progresso via logs ou GSD UI
                except GSDInvokerError as e:
                    # GSD invocation falhou, mas contexto foi criado
                    # Retorna sucesso parcial
                    return GSDConversionResult(
                        success=True,
                        element_name=element.source_name,
                        element_id=str(element.id),
                        context_path=files["context"],
                        branch_name=branch_name,
                        error=f"Contexto criado, mas GSD invocation falhou: {e}",
                        skipped_count=skipped_count,
                    )

            return GSDConversionResult(
                success=True,
                element_name=element.source_name,
                element_id=str(element.id),
                context_path=files["context"],
                branch_name=branch_name,
                skipped_count=skipped_count,
            )

        except Exception as e:
            import traceback
            return GSDConversionResult(
                success=False,
                element_name=element_name,
                error=f"Erro ao executar gsd-context: {str(e)}\n{traceback.format_exc()}",
                skipped_count=skipped_count,
            )

    async def _mark_item_skipped(self, item) -> None:
        """
        Marca um item como 'skipped' no MongoDB.

        Args:
            item: PendingItem a ser marcado
        """
        collection_map = {
            "elements": self.db.elements,
            "procedures": self.db.procedures,
            "class_definitions": self.db.class_definitions,
        }

        collection = collection_map.get(item.collection)
        if not collection:
            return

        # Atualizar status para 'skipped'
        if item.collection == "elements":
            # Elements usa DBRef para project_id
            await collection.update_one(
                {"_id": item.id},
                {"$set": {"conversion.status": "skipped"}},
            )
        else:
            # Outras collections usam ObjectId direto
            await collection.update_one(
                {"_id": item.id},
                {"$set": {"conversion.status": "skipped"}},
            )

    async def get_stats(self, project_name: str) -> dict:
        """
        Retorna estatísticas de conversão do projeto.

        Args:
            project_name: Nome do projeto

        Returns:
            Dict com estatísticas
        """
        return await self.tracker.get_stats(project_name)
