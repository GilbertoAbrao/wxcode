"""
API de Stacks.

Endpoints para listagem de stacks de tecnologia alvo.
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from wxcode.services import stack_service


router = APIRouter()


# === Response Models ===


class StackResponse(BaseModel):
    """Resposta de stack individual."""
    stack_id: str
    name: str
    group: str
    language: str
    framework: str
    orm: str
    template_engine: str

    class Config:
        from_attributes = True


class StackListResponse(BaseModel):
    """Lista de stacks."""
    stacks: list[StackResponse]
    total: int


class StacksGroupedResponse(BaseModel):
    """Stacks organizadas por categoria."""
    server_rendered: list[StackResponse]
    spa: list[StackResponse]
    fullstack: list[StackResponse]


# === Helper Functions ===


def _stack_to_response(stack) -> StackResponse:
    """Converte Stack document para StackResponse."""
    return StackResponse(
        stack_id=stack.stack_id,
        name=stack.name,
        group=stack.group,
        language=stack.language,
        framework=stack.framework,
        orm=stack.orm,
        template_engine=stack.template_engine,
    )


# === Endpoints ===


@router.get("/", response_model=StackListResponse)
async def list_stacks(
    group: Optional[str] = None,
    language: Optional[str] = None,
) -> StackListResponse:
    """
    Lista stacks com filtros opcionais.

    Filtros:
    - group: Categoria da stack (server-rendered, spa, fullstack)
    - language: Linguagem primaria (python, typescript, php, ruby)
    """
    stacks = await stack_service.list_stacks(group=group, language=language)

    return StackListResponse(
        stacks=[_stack_to_response(s) for s in stacks],
        total=len(stacks),
    )


@router.get("/grouped", response_model=StacksGroupedResponse)
async def get_stacks_grouped() -> StacksGroupedResponse:
    """
    Retorna stacks organizadas por categoria.

    Categorias:
    - server_rendered: FastAPI+HTMX, Django+HTMX, Rails, Laravel+Blade, etc.
    - spa: Next.js, Nuxt, SvelteKit, etc.
    - fullstack: NestJS+React, Laravel+Vue, etc.
    """
    grouped = await stack_service.get_stacks_grouped()

    return StacksGroupedResponse(
        server_rendered=[_stack_to_response(s) for s in grouped.get("server-rendered", [])],
        spa=[_stack_to_response(s) for s in grouped.get("spa", [])],
        fullstack=[_stack_to_response(s) for s in grouped.get("fullstack", [])],
    )
