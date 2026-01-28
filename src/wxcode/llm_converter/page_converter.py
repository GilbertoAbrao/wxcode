"""PageConverter - Orquestra a conversão de uma página WinDev para FastAPI."""

from datetime import datetime
from pathlib import Path

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from .context_builder import ContextBuilder
from .models import ConversionError, PageConversionResult
from .output_writer import OutputWriter
from .providers import LLMProvider, create_provider
from .response_parser import ResponseParser


class PageConverter:
    """Orquestra a conversão de uma página WinDev para FastAPI."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        output_dir: Path,
        llm_provider: LLMProvider | None = None,
        theme: str | None = None,
        project_root: Path | None = None,
    ):
        """Inicializa o PageConverter.

        Args:
            db: Conexão com banco MongoDB
            output_dir: Diretório de saída do projeto
            llm_provider: Provider LLM (opcional, cria AnthropicProvider se não fornecido)
            theme: Nome do tema para skills (ex: 'dashlite')
            project_root: Raiz do projeto para encontrar skills
        """
        self.db = db
        self.output_dir = Path(output_dir)
        self.theme = theme
        self.project_root = project_root
        self.context_builder = ContextBuilder(
            db, theme=theme, project_root=project_root
        )
        self.llm_provider = llm_provider or create_provider("anthropic")
        self.response_parser = ResponseParser()
        self.output_writer = OutputWriter(output_dir)

    async def convert(
        self,
        element_id: str | ObjectId,
        dry_run: bool = False,
    ) -> PageConversionResult:
        """Converte uma página completa.

        Args:
            element_id: ID do elemento no MongoDB
            dry_run: Se True, não escreve arquivos

        Returns:
            PageConversionResult com métricas e arquivos criados

        Raises:
            ConversionError: Se a conversão falhar
        """
        start_time = datetime.now()

        if isinstance(element_id, str):
            element_id = ObjectId(element_id)

        # 1. Construir contexto
        context = await self.context_builder.build(element_id)

        # 2. Chamar LLM
        llm_response = await self.llm_provider.convert(context)

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

        return PageConversionResult(
            element_id=str(element_id),
            page_name=result.page_name,
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
        page_name: str,
        project_name: str | None = None,
        dry_run: bool = False,
    ) -> PageConversionResult:
        """Converte uma página pelo nome.

        Args:
            page_name: Nome da página (ex: PAGE_Login)
            project_name: Nome do projeto (opcional)
            dry_run: Se True, não escreve arquivos

        Returns:
            PageConversionResult com métricas e arquivos criados

        Raises:
            ConversionError: Se a página não for encontrada
        """
        # Buscar elemento pelo nome
        query = {"source_name": page_name}
        if project_name:
            # Buscar projeto primeiro
            project = await self.db.projects.find_one({"name": project_name})
            if project:
                query["project_id"] = project["_id"]

        element = await self.db.elements.find_one(query)
        if not element:
            raise ConversionError(f"Page not found: {page_name}")

        return await self.convert(element["_id"], dry_run=dry_run)
