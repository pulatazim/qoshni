"""GET /categories va GET /districts — ro'yxatlar, o'zgarishsiz."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import SessionDep
from app.modules.catalog import service
from app.modules.catalog.schemas import CategoryRead, DistrictRead

router = APIRouter(tags=["catalog"])


@router.get("/categories", response_model=list[CategoryRead])
async def categories(session: SessionDep) -> list[CategoryRead]:
    return await service.list_categories(session)


@router.get("/districts", response_model=list[DistrictRead])
async def districts(session: SessionDep) -> list[DistrictRead]:
    return await service.list_districts(session)
