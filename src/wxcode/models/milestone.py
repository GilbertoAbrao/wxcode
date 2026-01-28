"""
Model de Milestone para rastreamento de conversao de elementos.

Representa um trabalho de conversao em um elemento especifico do Knowledge Base.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import Field


class MilestoneStatus(str, Enum):
    """Status do ciclo de vida de um Milestone."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Milestone(Document):
    """
    Representa um trabalho de conversao em um elemento KB.

    Milestones track the conversion of individual KB elements within an
    OutputProject. Each milestone triggers /wxcode:new-milestone workflow.
    """

    # Referencias (using PydanticObjectId to avoid extra queries)
    output_project_id: PydanticObjectId = Field(
        ...,
        description="Parent OutputProject reference"
    )
    element_id: PydanticObjectId = Field(
        ...,
        description="KB Element to convert"
    )

    # Identificacao (denormalized for display)
    element_name: str = Field(
        ...,
        description="Element name denormalized to avoid extra queries"
    )

    # Status
    status: MilestoneStatus = Field(
        default=MilestoneStatus.PENDING,
        description="Current status: pending | in_progress | completed | failed"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(
        default=None,
        description="When milestone was last updated"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When milestone completed (success or failure)"
    )

    class Settings:
        name = "milestones"
        use_state_management = True
        indexes = [
            "output_project_id",
            "element_id",
            "status",
            [("output_project_id", 1), ("status", 1)],
            [("output_project_id", 1), ("element_id", 1)],
        ]

    def __str__(self) -> str:
        return f"Milestone({self.element_name}, status={self.status.value})"
