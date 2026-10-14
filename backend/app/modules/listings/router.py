"""E'lon endpointlari: yaratish, lenta, tafsilot, holat, o'chirish."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.deps import CurrentUser, SessionDep
from app.core.errors import HTTP_UNPROCESSABLE, VALIDATION_ERROR, ApiError
from app.core.rate_limit import listing_quota, minute_quota
from app.models import Listing
from app.modules.listings import schemas, service
from app.modules.listings.service import DEFAULT_RADIUS_M
from app.modules.users.service import home_coordinates

router = APIRouter(prefix="/listings", tags=["listings"], dependencies=[Depends(minute_quota)])


def _to_read(listing: Listing) -> schemas.ListingRead:
    read = schemas.ListingRead.model_validate(listing)
    read.distance_m = getattr(listing, "distance_m", None)
    read.images = [schemas.image_read(image) for image in listing.images]
    return read


@router.post("", response_model=schemas.ListingRead, status_code=status.HTTP_201_CREATED)
async def create_listing(
    user: CurrentUser,
    payload: schemas.ListingCreate,
    session: SessionDep,
    _: None = Depends(listing_quota),
) -> schemas.ListingRead:
    listing = await service.create_listing(
        session,
        user,
        title=payload.title,
        description=payload.description,
        price=payload.price,
        price_type=payload.price_type,
        condition=payload.condition,
        category_id=payload.category_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    return _to_read(listing)


@router.get("", response_model=schemas.FeedPage)
async def list_feed(
    user: CurrentUser,
    session: SessionDep,
    radius: int = Query(default=DEFAULT_RADIUS_M, ge=1, le=service.MAX_RADIUS_M),
    category: int | None = Query(default=None),
    price_min: int | None = Query(default=None, ge=0),
    price_max: int | None = Query(default=None, ge=0),
    condition: schemas.Condition | None = Query(default=None),
    price_type: schemas.PriceType | None = Query(default=None),
    q: str | None = Query(default=None, min_length=2, max_length=80),
    sort: schemas.FeedSort = Query(default="new"),
    cursor: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
) -> schemas.FeedPage:
    """Radius ichidagi faol e'lonlar. Markaz: so'rov GPS'i yoki profil joylashuvi."""
    if latitude is None or longitude is None:
        home = await home_coordinates(session, user)
        if home is None:
            raise ApiError(
                VALIDATION_ERROR,
                "Lenta uchun joylashuv kerak: GPS'ni yoqing yoki profilga qo'shing",
                HTTP_UNPROCESSABLE,
            )
        latitude, longitude = home

    listings, next_cursor = await service.feed(
        session,
        latitude=latitude,
        longitude=longitude,
        radius_m=radius,
        category_id=category,
        price_min=price_min,
        price_max=price_max,
        condition=condition,
        price_type=price_type,
        query=q,
        sort=sort,
        cursor=cursor,
        limit=limit,
    )
    return schemas.FeedPage(items=[_to_read(item) for item in listings], next_cursor=next_cursor)


@router.get("/mine", response_model=schemas.FeedPage)
async def list_mine(
    user: CurrentUser,
    session: SessionDep,
    state: str | None = Query(default=None),
    cursor: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> schemas.FeedPage:
    listings, next_cursor = await service.list_mine(
        session, user, state=state, limit=limit, cursor=cursor
    )
    return schemas.FeedPage(items=[_to_read(item) for item in listings], next_cursor=next_cursor)


@router.get("/{listing_id}", response_model=schemas.ListingRead)
async def read_listing(
    listing_id: int, user: CurrentUser, session: SessionDep, response: Response
) -> schemas.ListingRead:
    listing = await service.get_listing(session, listing_id)
    await service.register_view(session, listing)
    return _to_read(listing)


@router.post("/{listing_id}/status", response_model=schemas.ListingRead)
async def change_listing_status(
    listing_id: int,
    payload: schemas.StatusUpdate,
    user: CurrentUser,
    session: SessionDep,
) -> schemas.ListingRead:
    listing = await service.get_listing(session, listing_id)
    listing = await service.change_status(session, user, listing, payload.status)
    return _to_read(listing)


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(listing_id: int, user: CurrentUser, session: SessionDep) -> None:
    listing = await service.get_listing(session, listing_id)
    await service.soft_delete(session, user, listing)
