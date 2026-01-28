"""Models para o conversor LLM de páginas WinDev para FastAPI + Jinja2."""

from typing import Any

from pydantic import BaseModel, Field


class ConversionContext(BaseModel):
    """Contexto para conversão de uma página."""

    page_name: str
    element_id: str
    controls: list[dict] = Field(default_factory=list)
    local_procedures: list[dict] = Field(default_factory=list)
    referenced_procedures: list[dict] = Field(default_factory=list)  # Procedures globais referenciadas
    dependencies: list[Any] = Field(default_factory=list)  # str ou dict
    estimated_tokens: int = 0
    theme: str | None = None  # Nome do tema (ex: 'dashlite')
    theme_skills: str | None = None  # Skills do tema carregados


class RouteDefinition(BaseModel):
    """Definição de rota FastAPI."""

    path: str
    methods: list[str]
    filename: str
    code: str


class TemplateDefinition(BaseModel):
    """Definição de template Jinja2."""

    filename: str
    content: str


class StaticFile(BaseModel):
    """Arquivo estático (CSS/JS)."""

    filename: str
    content: str


class DependencyList(BaseModel):
    """Dependências identificadas."""

    services: list[str] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)


class ConversionResult(BaseModel):
    """Resultado da conversão de uma página."""

    page_name: str
    route: RouteDefinition
    template: TemplateDefinition
    static_files: list[StaticFile] = Field(default_factory=list)
    dependencies: DependencyList = Field(default_factory=DependencyList)
    notes: list[str] = Field(default_factory=list)


class LLMResponse(BaseModel):
    """Resposta do LLM."""

    content: str
    input_tokens: int
    output_tokens: int


class PageConversionResult(BaseModel):
    """Resultado final da conversão de uma página."""

    element_id: str
    page_name: str
    files_created: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    tokens_used: dict = Field(default_factory=dict)
    duration_seconds: float = 0.0
    cost_usd: float = 0.0


class ProcedureContext(BaseModel):
    """Contexto para conversão de um procedure group."""

    group_name: str
    element_id: str
    source_file: str = ""
    procedures: list[dict] = Field(default_factory=list)
    referenced_procedures: list[dict] = Field(default_factory=list)
    estimated_tokens: int = 0


class ServiceMethod(BaseModel):
    """Definição de um método de service."""

    name: str
    params: list[dict] = Field(default_factory=list)
    return_type: str = "None"
    code: str = ""
    docstring: str = ""


class ServiceConversionResult(BaseModel):
    """Resultado da conversão de um procedure group para service."""

    class_name: str
    filename: str
    imports: list[str] = Field(default_factory=list)
    code: str = ""
    dependencies: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ProcedureConversionResult(BaseModel):
    """Resultado final da conversão de um procedure group."""

    element_id: str
    group_name: str
    class_name: str = ""
    files_created: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    tokens_used: dict = Field(default_factory=dict)
    duration_seconds: float = 0.0
    cost_usd: float = 0.0


class ConversionError(Exception):
    """Erro base de conversão."""

    pass


class ContextTooLargeError(ConversionError):
    """Contexto excede limite de tokens."""

    pass


class LLMResponseError(ConversionError):
    """Erro na resposta do LLM."""

    pass


class InvalidOutputError(ConversionError):
    """Output do LLM não passou na validação."""

    pass


class ProposalOutput(BaseModel):
    """Resultado da geração de proposal OpenSpec."""

    element_id: str
    element_name: str
    proposal_md: str
    tasks_md: str
    spec_md: str
    design_md: str | None = None
    missing_deps: list[str] = Field(default_factory=list)


class MappingDecision(BaseModel):
    """Decisão de mapeamento de um controle ou estrutura."""

    source_name: str
    source_type: str
    target_element: str
    target_type: str
    rationale: str = ""


class ConversionSpec(BaseModel):
    """Spec de conversão de um elemento."""

    source_element: str
    source_type: str
    target_files: list[str] = Field(default_factory=list)
    mapping_decisions: list[MappingDecision] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
