"""
Serviço para execução síncrona de conversões via spec-proposal.

Encapsula a lógica do comando CLI spec-proposal para ser chamado pela API.
"""

from pathlib import Path
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from wxcode.llm_converter import (
    ConversionTracker,
    SpecContextLoader,
    ProposalGenerator,
    ProposalOutput,
)
from wxcode.llm_converter.providers import create_provider, LLMProvider
from wxcode.models import Element


class ConversionExecutionResult:
    """Resultado da execução de uma conversão."""

    def __init__(
        self,
        success: bool,
        element_name: Optional[str] = None,
        element_id: Optional[str] = None,
        proposal_path: Optional[Path] = None,
        error: Optional[str] = None,
        specs_loaded: int = 0,
        missing_deps: int = 0,
    ):
        self.success = success
        self.element_name = element_name
        self.element_id = element_id
        self.proposal_path = proposal_path
        self.error = error
        self.specs_loaded = specs_loaded
        self.missing_deps = missing_deps


class ConversionExecutor:
    """
    Executor para conversões via spec-proposal.

    Encapsula toda a lógica de buscar próximo elemento,
    carregar specs, gerar proposal via LLM e atualizar status.
    """

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        output_base: Path,
        provider: str = "anthropic",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Inicializa o executor.

        Args:
            db: Database MongoDB
            output_base: Diretório base para output (ex: ./output/openspec)
            provider: Provider LLM ('anthropic', 'openai', 'ollama')
            model: Modelo específico (opcional)
            api_key: API key para o provider (opcional, usa variável de ambiente se não fornecida)
        """
        self.db = db
        self.output_base = Path(output_base)
        self.provider_name = provider
        self.model = model

        # Inicializar componentes
        self.tracker = ConversionTracker(db)
        self.specs_dir = self.output_base / "specs"
        self.spec_loader = SpecContextLoader(self.specs_dir)

        # Criar provider com API key se fornecida
        if api_key:
            self.llm_provider = create_provider(provider, model=model, api_key=api_key)
        else:
            self.llm_provider = create_provider(provider, model=model)

        self.generator = ProposalGenerator(self.llm_provider, self.output_base)

    async def execute_next_pending(
        self, project_name: str, max_skips: int = 100
    ) -> ConversionExecutionResult:
        """
        Executa conversão do próximo elemento pendente no projeto.

        Pula automaticamente items não suportados (classes, procedures)
        marcando-os como 'skipped' e busca o próximo válido.

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
                        return ConversionExecutionResult(
                            success=False,
                            error=f"Nenhum elemento suportado encontrado (pulados: {skipped_count} classes/procedures)",
                        )
                    return ConversionExecutionResult(
                        success=False,
                        error="Nenhum elemento pendente encontrado",
                    )

                # Por enquanto só suporta pages (elements collection)
                if item.collection != "elements":
                    # Marcar como skipped e buscar próximo
                    await self._mark_item_skipped(item)
                    skipped_count += 1
                    continue

                # Encontrou elemento suportado, executar conversão
                return await self.execute_element(str(item.id), item.name)

            # Excedeu limite de skips
            return ConversionExecutionResult(
                success=False,
                error=f"Excedido limite de {max_skips} items não suportados para pular",
            )

        except Exception as e:
            return ConversionExecutionResult(
                success=False,
                error=f"Erro ao executar conversão: {str(e)}",
            )

    async def execute_element(
        self, element_id: str, element_name: Optional[str] = None
    ) -> ConversionExecutionResult:
        """
        Executa conversão de um elemento específico.

        Args:
            element_id: ID do elemento no MongoDB
            element_name: Nome do elemento (opcional, para logging)

        Returns:
            Resultado da execução
        """
        try:
            # Carregar elemento
            element = await Element.get(element_id)
            if not element:
                return ConversionExecutionResult(
                    success=False,
                    error=f"Elemento {element_id} não encontrado",
                )

            # Carregar specs das dependências
            specs_content, missing_deps = self.spec_loader.load_dependency_specs(
                element
            )

            # Formatar contexto
            context = self.spec_loader.format_context(specs_content, missing_deps)

            # Gerar proposal via LLM
            proposal, proposal_path = await self.generator.generate_and_save(
                element, context
            )

            # Marcar status no tracker
            await self.tracker.mark_proposal_generated(element_id)

            return ConversionExecutionResult(
                success=True,
                element_name=element.source_name,
                element_id=element_id,
                proposal_path=proposal_path,
                specs_loaded=len(specs_content),
                missing_deps=len(missing_deps),
            )

        except Exception as e:
            return ConversionExecutionResult(
                success=False,
                element_id=element_id,
                element_name=element_name,
                error=f"Erro ao executar conversão: {str(e)}",
            )

    async def _mark_item_skipped(self, item) -> None:
        """
        Marca um item como 'skipped' no MongoDB.

        Args:
            item: PendingItem a ser marcado
        """
        from wxcode.llm_converter.conversion_tracker import PendingItem

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
