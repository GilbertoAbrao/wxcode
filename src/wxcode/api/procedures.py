"""
API de Procedures.
"""

from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from wxcode.models import Procedure


router = APIRouter()


class ProcedureResponse(BaseModel):
    """Resposta de procedure."""
    id: str
    name: str
    element_id: str
    code_lines: int
    is_public: bool
    is_internal: bool
    return_type: Optional[str]


class ProcedureListResponse(BaseModel):
    """Lista de procedures."""
    procedures: list[ProcedureResponse]
    total: int


@router.get("", response_model=ProcedureListResponse)
@router.get("/", response_model=ProcedureListResponse, include_in_schema=False)
async def list_procedures(
    element_id: Optional[str] = Query(None, description="Filter by element ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    is_local: Optional[bool] = Query(None, description="Filter by local/global"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> ProcedureListResponse:
    """Lista procedures com filtros opcionais."""
    query = {}

    if element_id:
        try:
            query["element_id"] = PydanticObjectId(element_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid element_id")

    if project_id:
        try:
            query["project_id"] = PydanticObjectId(project_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid project_id")

    if is_local is not None:
        query["is_local"] = is_local

    procedures = await Procedure.find(query).skip(skip).limit(limit).to_list()
    total = await Procedure.find(query).count()

    return ProcedureListResponse(
        procedures=[
            ProcedureResponse(
                id=str(p.id),
                name=p.name,
                element_id=str(p.element_id),
                code_lines=p.code_lines,
                is_public=p.is_public,
                is_internal=p.is_internal,
                return_type=p.return_type,
            )
            for p in procedures
        ],
        total=total,
    )


@router.get("/{procedure_id}", response_model=ProcedureResponse)
async def get_procedure(procedure_id: str) -> ProcedureResponse:
    """Busca uma procedure por ID."""
    try:
        proc = await Procedure.get(procedure_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid procedure ID")

    if not proc:
        raise HTTPException(status_code=404, detail="Procedure not found")

    return ProcedureResponse(
        id=str(proc.id),
        name=proc.name,
        element_id=str(proc.element_id),
        code_lines=proc.code_lines,
        is_public=proc.is_public,
        is_internal=proc.is_internal,
        return_type=proc.return_type,
    )
