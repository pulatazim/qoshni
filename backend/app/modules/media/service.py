"""Rasm quvuri: yuklangan faylni tozalash, qayta o'lchash va R2'ga yozish."""

from __future__ import annotations

import io
from dataclasses import dataclass

from fastapi import status
from PIL import Image, ImageOps
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import HTTP_UNPROCESSABLE, NOT_FOUND, VALIDATION_ERROR, ApiError
from app.core.storage import THUMB_EDGE, ObjectStorage, object_keys, thumb_key
from app.models import Listing, ListingImage

# Yuklash chegaralari: telefon rasmlari odatda 3-8 MB.
MAX_INPUT_BYTES = 10 * 1024 * 1024
MIN_EDGE = 80
MAX_IMAGES_PER_LISTING = 6
FULL_EDGE = 1080
WEBP_QUALITY = 82
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


@dataclass(frozen=True)
class Variant:
    width: int
    height: int
    data: bytes


def _prepare(image: Image.Image) -> Image.Image:
    """EXIF'ni tushirib qoladi, lekin burilishni rasmga singdiradi.

    EXIF'da GPS va telefon modeli bo'lishi mumkin — sotuvchining manzili
    ommaga chiqmasligi uchun metadata saqlanmaydi, faqat pikseller qoladi.
    """
    oriented = ImageOps.exif_transpose(image)
    if oriented.mode == "P":
        oriented = oriented.convert("RGBA")
    elif oriented.mode not in ("RGB", "RGBA"):
        oriented = oriented.convert("RGB")
    return oriented


def render_variants(data: bytes) -> list[Variant]:
    """Bitta rasmni ikki versiyaga bo'ladi: 1080 (ochilish) va 400 (lenta)."""
    if len(data) > MAX_INPUT_BYTES:
        raise ApiError(
            VALIDATION_ERROR,
            f"Rasm hajmi {MAX_INPUT_BYTES // (1024 * 1024)} MB dan oshmasin",
            HTTP_UNPROCESSABLE,
        )

    try:
        with Image.open(io.BytesIO(data)) as raw:
            if raw.format not in ALLOWED_FORMATS:
                raise ValueError("format")
            image = _prepare(raw)
            image.load()
    except Exception as exc:
        raise ApiError(
            VALIDATION_ERROR,
            "Faqat JPEG, PNG yoki WebP rasm yuklash mumkin",
            HTTP_UNPROCESSABLE,
        ) from exc

    if min(image.size) < MIN_EDGE:
        raise ApiError(VALIDATION_ERROR, "Rasm juda kichik", HTTP_UNPROCESSABLE)

    variants: list[Variant] = []
    for edge in (FULL_EDGE, THUMB_EDGE):
        scaled = image.copy()
        scaled.thumbnail((edge, edge), Image.LANCZOS)
        buffer = io.BytesIO()
        scaled.save(buffer, format="WEBP", quality=WEBP_QUALITY, method=4)
        variants.append(Variant(width=scaled.width, height=scaled.height, data=buffer.getvalue()))
    return variants


async def count_images(session: AsyncSession, listing_id: int) -> int:
    return (
        await session.scalar(
            select(func.count())
            .select_from(ListingImage)
            .where(ListingImage.listing_id == listing_id)
        )
        or 0
    )


async def add_image(
    session: AsyncSession,
    storage: ObjectStorage,
    listing: Listing,
    data: bytes,
) -> ListingImage:
    """Rasmni qayta ishlab, R2'ga yozib, `listing_images` ga qo'shadi."""
    existing = await count_images(session, listing.id)
    if existing >= MAX_IMAGES_PER_LISTING:
        raise ApiError(
            VALIDATION_ERROR,
            f"Bitta e'londa {MAX_IMAGES_PER_LISTING} tadan ko'p rasm bo'lmaydi",
            HTTP_UNPROCESSABLE,
        )

    variants = render_variants(data)
    full, thumb = variants
    base_key, small_key = object_keys()
    await storage.put(base_key, full.data, "image/webp")
    await storage.put(small_key, thumb.data, "image/webp")

    # Birinchi rasm muqova bo'ladi — keyin qo'shilganlar position bilan ortga boradi.
    image = ListingImage(
        listing_id=listing.id,
        storage_key=base_key,
        width=full.width,
        height=full.height,
        position=existing,
    )
    session.add(image)
    await session.commit()
    await session.refresh(image)
    return image


async def get_image(session: AsyncSession, listing: Listing, image_id: int) -> ListingImage:
    image = await session.scalar(
        select(ListingImage).where(
            ListingImage.id == image_id, ListingImage.listing_id == listing.id
        )
    )
    if image is None:
        raise ApiError(NOT_FOUND, "Rasm topilmadi", status.HTTP_404_NOT_FOUND)
    return image


async def remove_image(session: AsyncSession, storage: ObjectStorage, image: ListingImage) -> None:
    await storage.delete(image.storage_key)
    await storage.delete(thumb_key(image.storage_key))
    await session.delete(image)
    await session.commit()
