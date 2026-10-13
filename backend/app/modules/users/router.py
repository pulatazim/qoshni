"""O'z profili uchun endpointlar: GET /me, PATCH /me, PUT /me/location."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentUser, SessionDep
from app.modules.users import schemas
from app.modules.users.service import update_location

router = APIRouter(tags=["users"])


@router.get("/me", response_model=schemas.UserRead)
async def read_me(user: CurrentUser) -> schemas.UserRead:
    return schemas.UserRead.model_validate(user)


@router.patch("/me", response_model=schemas.UserRead)
async def patch_me(
    user: CurrentUser, payload: schemas.UserUpdate, session: SessionDep
) -> schemas.UserRead:
    changed = payload.model_dump(exclude_unset=True)
    for field, value in changed.items():
        setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return schemas.UserRead.model_validate(user)


@router.put("/me/location", response_model=schemas.UserRead)
async def put_me_location(
    user: CurrentUser,
    payload: schemas.LocationUpdate,
    session: SessionDep,
) -> schemas.UserRead:
    await update_location(
        session,
        user,
        latitude=payload.latitude,
        longitude=payload.longitude,
        district_id=payload.district_id,
    )
    return schemas.UserRead.model_validate(user)
