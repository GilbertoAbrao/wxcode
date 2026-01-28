"""FastAPI + Jinja2 code generators for wxcode.

This module provides generators that transform the WinDev/WebDev knowledge base
stored in MongoDB into a complete FastAPI + Jinja2 application.

Generators:
    - SchemaGenerator: Generates Pydantic models from DatabaseSchema
    - DomainGenerator: Generates Python classes from ClassDefinition
    - ServiceGenerator: Generates FastAPI services from Procedures
    - RouteGenerator: Generates FastAPI routes for pages
    - APIGenerator: Generates REST API routes from wdrest
    - TemplateGenerator: Generates Jinja2 templates from pages/controls

Selective Conversion:
    Use ElementFilter to convert specific elements:

    from wxcode.generator import GeneratorOrchestrator, ElementFilter

    # Convert only specific elements by name pattern
    filter = ElementFilter(element_names=["PAGE_Login", "PAGE_Home*"])
    orchestrator = GeneratorOrchestrator(project_id, output_dir, filter)
    result = await orchestrator.generate_all()

Usage:
    from wxcode.generator import GeneratorOrchestrator, GenerationResult

    orchestrator = GeneratorOrchestrator(project_id, output_dir)
    result = await orchestrator.generate_all()
    print(result.summary())
"""

from .api_generator import APIGenerator
from .base import BaseGenerator, ElementFilter
from .domain_generator import DomainGenerator
from .orchestrator import GeneratorOrchestrator, OrchestratorResult
from .result import GenerationResult
from .route_generator import RouteGenerator
from .schema_generator import SchemaGenerator
from .service_generator import ServiceGenerator
from .starter_kit import StarterKitGenerator
from .template_generator import TemplateGenerator
from .wlanguage_converter import ConversionResult, WLanguageConverter, convert_wlanguage

__all__ = [
    "APIGenerator",
    "BaseGenerator",
    "ConversionResult",
    "DomainGenerator",
    "ElementFilter",
    "GenerationResult",
    "GeneratorOrchestrator",
    "OrchestratorResult",
    "RouteGenerator",
    "SchemaGenerator",
    "ServiceGenerator",
    "StarterKitGenerator",
    "TemplateGenerator",
    "WLanguageConverter",
    "convert_wlanguage",
]
