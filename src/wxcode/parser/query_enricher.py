"""
Query Enricher para projetos WebDev.

Enriquece elementos do tipo query com SQL extraído do PDF de documentação.
"""

import logging
from pathlib import Path
from typing import Optional

from bson import ObjectId

from wxcode.models import Element, ElementAST, ElementType
from wxcode.parser.query_parser import QueryParser

logger = logging.getLogger(__name__)


class QueryEnricher:
    """
    Enriquece elementos do tipo query com SQL do PDF de documentação.

    Similar ao ElementEnricher para páginas, mas focado em queries.
    """

    def __init__(self, project_id: ObjectId, pdf_docs_dir: Path):
        """
        Inicializa o enricher.

        Args:
            project_id: ID do projeto no MongoDB
            pdf_docs_dir: Diretório com PDFs de documentação splitados
        """
        self.project_id = project_id
        self.pdf_docs_dir = pdf_docs_dir
        self.queries_dir = pdf_docs_dir / "queries"
        self.parser = QueryParser()

        self.stats = {
            "total_queries": 0,
            "enriched": 0,
            "pdf_not_found": 0,
            "sql_not_found": 0,
            "errors": 0
        }

    async def enrich_all(self) -> dict:
        """
        Enriquece todas as queries do projeto.

        Returns:
            Estatísticas do processamento
        """
        # Busca todas as queries do projeto
        queries = await Element.find(
            Element.project_id == self.project_id,
            Element.source_type == ElementType.QUERY
        ).to_list()

        self.stats["total_queries"] = len(queries)

        logger.info(f"Encontradas {len(queries)} queries para enriquecer")

        for query in queries:
            try:
                await self._enrich_query(query)
            except Exception as e:
                logger.error(f"Erro ao enriquecer query {query.source_name}: {e}")
                self.stats["errors"] += 1

        logger.info(
            f"Enriquecimento completo: {self.stats['enriched']}/{self.stats['total_queries']} queries"
        )

        return self.stats

    async def _enrich_query(self, query: Element):
        """
        Enriquece uma query individual.

        Args:
            query: Elemento da query
        """
        # Busca PDF correspondente
        pdf_path = self.queries_dir / f"{query.source_name}.pdf"

        if not pdf_path.exists():
            logger.warning(f"PDF não encontrado para query {query.source_name}")
            self.stats["pdf_not_found"] += 1
            return

        try:
            # Parseia SQL do PDF
            query_info = self.parser.parse(pdf_path)

            # Atualiza elemento
            if query_info.has_sql:
                # Cria AST se não existe
                if query.ast is None:
                    query.ast = ElementAST()

                # Popula campos do AST
                query.ast.sql = query_info.sql
                query.ast.parameters = query_info.parameters
                query.ast.tables = query_info.tables
                query.ast.incomplete = False

                # Popula raw_content com SQL
                query.raw_content = query_info.sql

                # Atualiza dependências (tabelas)
                if query_info.tables:
                    # Adiciona tabelas às dependências
                    existing_tables = set(query.dependencies.data_files or [])
                    existing_tables.update(query_info.tables)
                    query.dependencies.data_files = sorted(list(existing_tables))

                await query.save()

                logger.info(
                    f"Query {query.source_name} enriquecida: "
                    f"{len(query_info.parameters)} params, {len(query_info.tables)} tables"
                )
                self.stats["enriched"] += 1

            else:
                # SQL não encontrado
                logger.warning(f"SQL não encontrado no PDF para query {query.source_name}")

                if query.ast is None:
                    query.ast = ElementAST()

                query.ast.incomplete = True
                await query.save()

                self.stats["sql_not_found"] += 1

        except Exception as e:
            logger.error(f"Erro ao parsear query {query.source_name}: {e}")
            raise
