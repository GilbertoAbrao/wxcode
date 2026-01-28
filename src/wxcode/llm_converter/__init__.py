"""LLM-based page converter for WinDev/WebDev to FastAPI + Jinja2."""

from .context_builder import ContextBuilder
from .llm_client import LLMClient  # DEPRECATED - use create_provider() instead
from .import_validator import ImportValidator
from .output_writer import OutputWriter
from .page_converter import PageConverter
from .response_parser import ResponseParser
from .procedure_context_builder import ProcedureContextBuilder
from .procedure_converter import ProcedureConverter
from .service_response_parser import ServiceResponseParser
from .service_output_writer import ServiceOutputWriter
from .spec_context_loader import SpecContextLoader
from .proposal_generator import ProposalGenerator
from .conversion_tracker import ConversionTracker
from .models import (
    ConversionContext,
    ConversionError,
    ConversionResult,
    ConversionSpec,
    ContextTooLargeError,
    DependencyList,
    InvalidOutputError,
    LLMResponse,
    LLMResponseError,
    MappingDecision,
    PageConversionResult,
    ProcedureContext,
    ProcedureConversionResult,
    ProposalOutput,
    RouteDefinition,
    ServiceConversionResult,
    StaticFile,
    TemplateDefinition,
)
from .providers import (
    LLMProvider,
    AnthropicProvider,
    OpenAIProvider,
    OllamaProvider,
    create_provider,
    list_providers,
)

__all__ = [
    # Page conversion components
    "ContextBuilder",
    "ImportValidator",
    "OutputWriter",
    "PageConverter",
    "ResponseParser",
    # Procedure/Service conversion components
    "ProcedureContextBuilder",
    "ProcedureConverter",
    "ServiceResponseParser",
    "ServiceOutputWriter",
    # Incremental conversion components
    "SpecContextLoader",
    "ProposalGenerator",
    "ConversionTracker",
    # Provider abstraction
    "LLMProvider",
    "AnthropicProvider",
    "OpenAIProvider",
    "OllamaProvider",
    "create_provider",
    "list_providers",
    # Deprecated
    "LLMClient",  # DEPRECATED - use create_provider('anthropic') instead
    # Models - Page
    "ConversionContext",
    "ConversionError",
    "ConversionResult",
    "ContextTooLargeError",
    "DependencyList",
    "InvalidOutputError",
    "LLMResponse",
    "LLMResponseError",
    "PageConversionResult",
    "RouteDefinition",
    "StaticFile",
    "TemplateDefinition",
    # Models - Procedure/Service
    "ProcedureContext",
    "ProcedureConversionResult",
    "ServiceConversionResult",
    # Models - Incremental conversion
    "ProposalOutput",
    "ConversionSpec",
    "MappingDecision",
]
