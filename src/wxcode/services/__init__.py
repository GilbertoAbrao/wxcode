"""
Serviços de negócio do wxcode.
"""

from wxcode.services.project_service import (
    purge_project,
    purge_project_by_name,
    check_duplicate_projects,
    PurgeStats,
)
from wxcode.services.conversion_executor import (
    ConversionExecutor,
    ConversionExecutionResult,
)
from wxcode.services.workspace_manager import WorkspaceManager
from wxcode.services.stack_service import (
    seed_stacks,
    get_stack_by_id,
    list_stacks,
    get_stacks_grouped,
)
from wxcode.services.schema_extractor import (
    extract_schema_for_configuration,
    get_element_count_for_configuration,
)
from wxcode.services.prompt_builder import PromptBuilder

__all__ = [
    # Project service
    "purge_project",
    "purge_project_by_name",
    "check_duplicate_projects",
    "PurgeStats",
    # Conversion
    "ConversionExecutor",
    "ConversionExecutionResult",
    # Workspace
    "WorkspaceManager",
    # Stack service
    "seed_stacks",
    "get_stack_by_id",
    "list_stacks",
    "get_stacks_grouped",
    # Schema extractor
    "extract_schema_for_configuration",
    "get_element_count_for_configuration",
    # Prompt builder
    "PromptBuilder",
]
