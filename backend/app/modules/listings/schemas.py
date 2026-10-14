"""E'lonlarning API sxemalari."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.storage import public_url, thumb_url
from app.models import ListingImage

PriceType = Literal["fixed", "negotiable", "free"]
Condition = Literal["new", "used"]
FeedSort = Literal["new", "cheap", "expensive"]
NewStatus = Literal["active", "reserved", "sold", "hidden"]


class ListingCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    description: str = Field(default="", max_length=1000)
    price: int = Field(default=0, ge=0, le=10_000_000_000)
    price_type: PriceType = "fixed"
    condition: Condition = "used"
    category_id: int
    # GPS bo'lmasa foydalanuvchining saqlangan joylashuvi ishlatiladi.
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class ListingImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    storage_key: str
    width: int | None
    height: int | None
    position: int
    # Manzillar R2 public base'dan hisoblanadi (DB'da saqlanmaydi).
    url: str = ""
    thumb_url: str = ""


def image_read(image: ListingImage) -> ListingImageRead:
    """Model → sxem, rasm manzillari bilan."""
    return ListingImageRead(
        id=image.id,
        storage_key=image.storage_key,
        width=image.width,
        height=image.height,
        position=image.position,
        url=public_url(image.storage_key),
        thumb_url=thumb_url(image.storage_key),
    )


class ListingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    seller_id: int
    category_id: int
    title: str
    description: str
    price: int
    price_type: str
    condition: str
    status: str
    district_id: int | None
    view_count: int
    images: list[ListingImageRead] = []
    # Lenta uchun hisoblanadi, DB'da saqlanmaydi.
    distance_m: float | None = None


class StatusUpdate(BaseModel):
    """Holatni qo'lda almashtirish: sotildi / band / yashirin / faol."""

    status: NewStatus


class FeedPage(BaseModel):
    items: list[ListingRead]
    next_cursor: str | None = None
