"""
Model de Stack para definicao de tecnologias alvo.

Representa uma combinacao de tecnologias (framework, ORM, template engine)
que Claude Code usa para gerar codigo idiomatico.
"""

from beanie import Document
from pydantic import Field


class Stack(Document):
    """
    Define caracteristicas de uma stack de tecnologia alvo.

    Stack metadata is passed to Claude Code via /wxcode:new-project prompt,
    enabling LLM-driven generation of idiomatic code for the target stack.
    """

    # Identificacao
    stack_id: str = Field(
        ...,
        description="Unique identifier like 'fastapi-htmx'"
    )
    name: str = Field(
        ...,
        description="Display name like 'FastAPI + HTMX'"
    )

    # Categorias
    group: str = Field(
        ...,
        description="Category: 'server-rendered' | 'spa' | 'fullstack'"
    )
    language: str = Field(
        ...,
        description="Primary language: 'python' | 'typescript' | 'php' | 'ruby'"
    )
    framework: str = Field(
        ...,
        description="Backend framework: 'fastapi' | 'django' | 'laravel' | etc."
    )

    # Persistencia
    orm: str = Field(
        ...,
        description="ORM: 'sqlalchemy' | 'django-orm' | 'eloquent' | etc."
    )
    orm_pattern: str = Field(
        ...,
        description="ORM pattern: 'active-record' | 'data-mapper' | 'repository'"
    )

    # Templates
    template_engine: str = Field(
        ...,
        description="Template engine: 'jinja2' | 'blade' | 'erb' | 'jsx' | etc."
    )

    # Estrutura e convencoes
    file_structure: dict[str, str] = Field(
        default_factory=dict,
        description="Path templates: { 'models': 'app/models/', 'routes': 'app/routes/' }"
    )
    naming_conventions: dict[str, str] = Field(
        default_factory=dict,
        description="Naming rules: { 'class': 'PascalCase', 'file': 'snake_case' }"
    )
    type_mappings: dict[str, str] = Field(
        default_factory=dict,
        description="HyperFile to target types: { 'string': 'str', 'integer': 'int' }"
    )

    # Templates de codigo
    imports_template: str = Field(
        default="",
        description="Common imports for models"
    )
    model_template: str = Field(
        default="",
        description="Example model structure for reference"
    )

    # Optional stack-specific extensions
    htmx_patterns: dict[str, str] = Field(
        default_factory=dict,
        description="HTMX-specific patterns for server-rendered stacks"
    )
    typescript_types: dict[str, str] = Field(
        default_factory=dict,
        description="HyperFile to TypeScript types for SPA frontend"
    )

    class Settings:
        name = "stacks"
        use_state_management = True
        indexes = [
            "stack_id",
            "group",
            "language",
            [("group", 1), ("language", 1)],
        ]

    def __str__(self) -> str:
        return f"Stack({self.stack_id}: {self.name})"
