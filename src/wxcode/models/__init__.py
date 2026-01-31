"""
Models Pydantic/Beanie para MongoDB.
"""

from wxcode.models.project import Project, ProjectConfiguration, ProjectStatus
from wxcode.models.element import (
    Element,
    ElementType,
    ElementLayer,
    ElementChunk,
    ElementAST,
    ElementDependencies,
    ElementConversion,
    ConversionStatus,
)
from wxcode.models.conversion import Conversion, ConversionError, ConversionPhase
from wxcode.models.control_type import (
    ControlTypeDefinition,
    PREFIX_TO_TYPE_NAME,
    CONTAINER_PREFIXES,
    infer_type_name_from_prefix,
    is_container_by_prefix,
)
from wxcode.models.control import (
    Control,
    ControlEvent,
    ControlProperties,
    DataBindingInfo,
    DataBindingType,
    EVENT_TYPE_CODES,
    get_event_name,
)
from wxcode.models.procedure import (
    Procedure,
    ProcedureParameter,
    ProcedureDependencies,
)
from wxcode.models.schema import (
    DatabaseSchema,
    SchemaConnection,
    SchemaTable,
    SchemaColumn,
    SchemaIndex,
)
from wxcode.models.class_definition import (
    ClassDefinition,
    ClassMember,
    ClassMethod,
    ClassConstant,
    ClassDependencies,
)
from wxcode.models.token_usage import TokenUsageLog
from wxcode.models.product import Product, ProductType, ProductStatus
from wxcode.models.conversion_history import ConversionHistoryEntry
from wxcode.models.stack import Stack, StartDevTemplate
from wxcode.models.output_project import OutputProject, OutputProjectStatus
from wxcode.models.milestone import Milestone, MilestoneStatus

__all__ = [
    # Project
    "Project",
    "ProjectConfiguration",
    "ProjectStatus",
    # Element
    "Element",
    "ElementType",
    "ElementLayer",
    "ElementChunk",
    "ElementAST",
    "ElementDependencies",
    "ElementConversion",
    "ConversionStatus",
    # Conversion
    "Conversion",
    "ConversionError",
    "ConversionPhase",
    # ControlType
    "ControlTypeDefinition",
    "PREFIX_TO_TYPE_NAME",
    "CONTAINER_PREFIXES",
    "infer_type_name_from_prefix",
    "is_container_by_prefix",
    # Control
    "Control",
    "ControlEvent",
    "ControlProperties",
    "DataBindingInfo",
    "DataBindingType",
    "EVENT_TYPE_CODES",
    "get_event_name",
    # Procedure
    "Procedure",
    "ProcedureParameter",
    "ProcedureDependencies",
    # Schema
    "DatabaseSchema",
    "SchemaConnection",
    "SchemaTable",
    "SchemaColumn",
    "SchemaIndex",
    # ClassDefinition
    "ClassDefinition",
    "ClassMember",
    "ClassMethod",
    "ClassConstant",
    "ClassDependencies",
    # TokenUsage
    "TokenUsageLog",
    # Product
    "Product",
    "ProductType",
    "ProductStatus",
    # ConversionHistory
    "ConversionHistoryEntry",
    # v4 Models
    "Stack",
    "OutputProject",
    "OutputProjectStatus",
    "Milestone",
    "MilestoneStatus",
]
