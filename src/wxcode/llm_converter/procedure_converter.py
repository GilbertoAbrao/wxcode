"""ProcedureConverter - Orquestra a conversão de um procedure group para service Python."""

from datetime import datetime
from pathlib import Path

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from .models import ConversionError, ProcedureConversionResult
from .procedure_context_builder import ProcedureContextBuilder
from .providers import LLMProvider, create_provider
from .service_output_writer import ServiceOutputWriter
from .service_response_parser import ServiceResponseParser


class ProcedureConverter:
    """Orquestra a conversão de um procedure group para service Python."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        output_dir: Path,
        llm_provider: LLMProvider | None = None,
    ):
        """Inicializa o ProcedureConverter.

        Args:
            db: Conexão com banco MongoDB
            output_dir: Diretório de saída do projeto
            llm_provider: Provider LLM (opcional, cria AnthropicProvider se não fornecido)
        """
        self.db = db
        self.output_dir = Path(output_dir)
        self.context_builder = ProcedureContextBuilder(db)
        self.llm_provider = llm_provider or create_provider("anthropic")
        self.response_parser = ServiceResponseParser()
        self.output_writer = ServiceOutputWriter(output_dir)

    async def convert(
        self,
        element_id: str | ObjectId,
        dry_run: bool = False,
    ) -> ProcedureConversionResult:
        """Converte um procedure group completo.

        Args:
            element_id: ID do elemento no MongoDB
            dry_run: Se True, não escreve arquivos

        Returns:
            ProcedureConversionResult com métricas e arquivos criados

        Raises:
            ConversionError: Se a conversão falhar
        """
        start_time = datetime.now()

        if isinstance(element_id, str):
            element_id = ObjectId(element_id)

        # 1. Construir contexto
        context = await self.context_builder.build(element_id)

        # 2. Chamar LLM
        llm_response = await self.llm_provider.convert_procedure(context)

        # 3. Parsear resposta
        result = self.response_parser.parse(llm_response.content)

        # 4. Escrever arquivos (se não for dry_run)
        files_created: list[str] = []
        if not dry_run:
            paths = await self.output_writer.write(result)
            files_created = [str(p) for p in paths]

        # 5. Calcular métricas
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        cost = self.llm_provider.estimate_cost(
            llm_response.input_tokens,
            llm_response.output_tokens
        )

        return ProcedureConversionResult(
            element_id=str(element_id),
            group_name=context.group_name,
            class_name=result.class_name,
            files_created=files_created,
            notes=result.notes,
            tokens_used={
                "input": llm_response.input_tokens,
                "output": llm_response.output_tokens,
                "total": llm_response.input_tokens + llm_response.output_tokens,
            },
            duration_seconds=duration,
            cost_usd=cost,
        )

    async def convert_by_name(
        self,
        group_name: str,
        project_name: str | None = None,
        dry_run: bool = False,
    ) -> ProcedureConversionResult:
        """Converte um procedure group pelo nome.

        Args:
            group_name: Nome do grupo (ex: ServerProcedures)
            project_name: Nome do projeto (opcional)
            dry_run: Se True, não escreve arquivos

        Returns:
            ProcedureConversionResult com métricas e arquivos criados

        Raises:
            ConversionError: Se o grupo não for encontrado
        """
        # Buscar elemento pelo nome (pode ter extensão .wdg ou não)
        query = {
            "$or": [
                {"source_name": group_name},
                {"source_name": f"{group_name}.wdg"},
            ],
            "source_type": "procedure_group"
        }
        if project_name:
            # Buscar projeto primeiro
            project = await self.db.projects.find_one({"name": project_name})
            if project:
                query["project_id"] = project["_id"]

        element = await self.db.elements.find_one(query)
        if not element:
            raise ConversionError(f"Procedure group not found: {group_name}")

        return await self.convert(element["_id"], dry_run=dry_run)
