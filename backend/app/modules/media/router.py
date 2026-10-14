"""E'lon rasmlari: yuklash, ro'yxat va o'chirish."""

from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile, status

from app.core.deps import CurrentUser, SessionDep, StorageDep
from app.core.rate_limit import minute_quota
from app.modules.listings.schemas import ListingImageRead, image_read
from app.modules.listings.service import get_owned_listing
from app.modules.media import service

# Rasm yuklash ham qimmat amal — daqiqalik limitga kiradi.
router = APIRouter(
    prefix="/listings/{listing_id}/images",
    tags=["media"],
    dependencies=[Depends(minute_quota)],
)


@router.post("", response_model=ListingImageRead, status_code=status.HTTP_201_CREATED)
async def upload_image(
    listing_id: int,
    file: UploadFile,
    user: CurrentUser,
    session: SessionDep,
    storage: StorageDep,
) -> ListingImageRead:
    """Rasmni qabul qilib, tozalab-websizlab R2'ga yozadi va e'longa biriktiradi."""
    listing = await get_owned_listing(session, user, listing_id)
    data = await file.read()
    image = await service.add_image(session, storage, listing, data)
    return image_read(image)


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    listing_id: int,
    image_id: int,
    user: CurrentUser,
    session: SessionDep,
    storage: StorageDep,
) -> None:
    listing = await get_owned_listing(session, user, listing_id)
    image = await service.get_image(session, listing, image_id)
    await service.remove_image(session, storage, image)
