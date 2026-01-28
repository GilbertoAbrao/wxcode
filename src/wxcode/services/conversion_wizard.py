"""
Conversion Wizard Service - Orchestrates element conversion with checkpoints.

This service:
1. Creates isolated conversion workspace in {workspace_path}/conversion/
2. Sets up .planning/ directory structure for GSD
3. Collects element context via GSDContextCollector
4. Creates CONTEXT.md in the conversion directory
5. Configures GSDInvoker with correct cwd
"""

from datetime import datetime
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

from wxcode.models import Element, Project
from wxcode.models.product import Product
from wxcode.services.gsd_context_collector import GSDContextCollector, GSDContextWriter
from wxcode.services.workspace_manager import WorkspaceManager


class ConversionWizardError(Exception):
    """Erro no wizard de conversao."""
    pass


class ConversionWizard:
    """Orchestrates element conversion via GSD workflow."""

    def __init__(self, product: Product, project: Project):
        """
        Args:
            product: Product instance to convert
            project: Project instance
        """
        self.product = product
        self.project = project
        self.workspace_path = Path(product.workspace_path)

    async def setup_conversion_workspace(
        self,
        element_names: list[str],
        mongo_client: AsyncIOMotorClient,
        neo4j_conn=None,
    ) -> Path:
        """
        Creates conversion workspace with CONTEXT.md for selected elements.

        IMPORTANT: Creates .planning/ in workspace/conversion/, NOT project root.
        This ensures isolation per CONV-02 requirement.

        Args:
            element_names: Elements to convert (uses first for context)
            mongo_client: MongoDB client for context collection
            neo4j_conn: Optional Neo4j connection for dependency analysis

        Returns:
            Path to conversion directory with CONTEXT.md

        Raises:
            ConversionWizardError: If element not found or context collection fails
        """
        # 1. Ensure product directory exists
        conversion_dir = WorkspaceManager.ensure_product_directory(
            self.workspace_path, "conversion"
        )

        # 2. Create .planning structure for GSD (CRITICAL for CONV-02)
        planning_dir = conversion_dir / ".planning"
        planning_dir.mkdir(exist_ok=True)
        (planning_dir / "phases").mkdir(exist_ok=True)

        # 3. Validate element exists
        if not element_names:
            raise ConversionWizardError("Nenhum elemento especificado para conversao")

        element_name = element_names[0]  # GSD handles one at a time

        # 4. Collect context using existing service
        collector = GSDContextCollector(mongo_client, neo4j_conn)
        try:
            context_data = await collector.collect(
                element_name=element_name,
                project_name=self.project.name,
                depth=2,
            )
        except ValueError as e:
            raise ConversionWizardError(f"Elemento nao encontrado: {e}")
        except Exception as e:
            raise ConversionWizardError(f"Erro ao coletar contexto: {e}")

        # 5. Write context files to conversion directory
        writer = GSDContextWriter(conversion_dir)
        writer.write_all(context_data, branch_name="main")

        # 6. Update product with output directory
        self.product.output_directory = str(conversion_dir)
        self.product.updated_at = datetime.utcnow()
        await self.product.save()

        return conversion_dir

    @staticmethod
    def get_gsd_invoker(conversion_dir: Path):
        """
        Creates GSDInvoker configured for conversion workspace.

        CRITICAL (CONV-03): cwd is set to conversion_dir so .planning/
        is created there, not in project root.

        Args:
            conversion_dir: Path to workspace/conversion/ directory

        Returns:
            Configured GSDInvoker instance

        Raises:
            ValueError: If CONTEXT.md not found
        """
        from wxcode.services.gsd_invoker import GSDInvoker

        context_md = conversion_dir / "CONTEXT.md"
        if not context_md.exists():
            raise ValueError(f"CONTEXT.md nao encontrado em {conversion_dir}")

        return GSDInvoker(
            context_md_path=context_md,
            working_dir=conversion_dir,  # CRITICAL: GSD runs HERE
        )

    async def validate_elements(
        self,
        element_names: list[str],
    ) -> list[Element]:
        """
        Validates that all specified elements exist in the project.

        Args:
            element_names: List of element source_names to validate

        Returns:
            List of Element objects

        Raises:
            ConversionWizardError: If any element not found
        """
        elements = []
        missing = []

        for name in element_names:
            element = await Element.find_one(
                {
                    "project_id.$id": self.project.id,
                    "source_name": name,
                }
            )
            if element:
                elements.append(element)
            else:
                missing.append(name)

        if missing:
            raise ConversionWizardError(
                f"Elementos nao encontrados: {', '.join(missing)}"
            )

        return elements
