"""Rasm quvuri testlari: EXIF tozalash, o'lcham, yuklash API'si.

R2 kalitlari testlarda ishlatilmaydi — `storage` fixture'i xotidagi saqlagichni beradi.
"""

from __future__ import annotations

import io

from PIL import Image

from app.core.errors import ApiError
from app.modules.media import service
from app.modules.media.service import render_variants

# Test rasmlari katta bo'lib ketmasligi uchun kichik, lekin real o'lcham nisbati.
SOURCE_SIZE = (1600, 1200)


def jpeg_bytes(size=SOURCE_SIZE, orientation: int | None = None, meta: bool = True) -> bytes:
    """EXIF sahifasi bo'lgan rasm yasaydi.

    Pillow ichma-ich GPS IFD yozishni qo'llab-quvvatlamaydi, shuning uchun GPS'ni
    alohida belgilamaymiz: butun EXIF bloki tashlab yuboriladi, GPS ham shu yerda.
    """
    image = Image.new("RGB", size, (180, 40, 40))
    exif = Image.Exif()
    if orientation:
        exif[0x0112] = orientation
    if meta:
        exif[0x010F] = "Make-A"
        exif[0x0131] = "Telegram Android"
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", exif=exif if (orientation or meta) else None)
    return buffer.getvalue()


def test_variants_are_webp_and_resized() -> None:
    full, thumb = render_variants(jpeg_bytes())

    assert (full.width, full.height) == (1080, 810)
    assert (thumb.width, thumb.height) == (400, 300)
    for variant in (full, thumb):
        assert variant.data[:4] == b"RIFF" and variant.data[8:12] == b"WEBP"
    assert len(thumb.data) < len(full.data)


def test_exif_metadata_is_stripped() -> None:
    """Manzil (GPS) va kamera ma'lumotlari foydalanuvchini himoya qilish uchun tashlanadi."""
    source = Image.open(io.BytesIO(jpeg_bytes()))
    assert source.getexif()[0x0131] == "Telegram Android"

    full, _ = render_variants(jpeg_bytes())
    assert not Image.open(io.BytesIO(full.data)).getexif()


def test_orientation_is_baked_into_pixels() -> None:
    """EXIF'dagi "burilgan" rasm pikselleri ham buriladi — aks holda rasm chala bo'ladi."""
    rotated = jpeg_bytes(size=(1200, 1600), orientation=6, meta=False)
    before = Image.open(io.BytesIO(rotated))
    full, _ = render_variants(rotated)

    assert before.width < before.height  # fayl to'g'ri holatda, EXIF 90° deydi
    assert full.width > full.height  # biz piksellarni burdik — balandlik kichraydi


def test_small_source_is_not_upscaled() -> None:
    full, thumb = render_variants(jpeg_bytes(size=(600, 400)))
    assert (full.width, full.height) == (600, 400)
    assert (thumb.width, thumb.height) == (400, 267)


def test_non_image_is_rejected() -> None:
    try:
        render_variants(b"bu rasm emas, oddiy matn")
    except ApiError as exc:
        assert exc.code == "validation_error"
    else:
        raise AssertionError("rasm bo'lmagan fayl qabul qilinmadi")


def test_oversized_file_is_rejected() -> None:
    huge = b"\xff" * (service.MAX_INPUT_BYTES + 1)
    try:
        render_variants(huge)
    except ApiError as exc:
        assert "MB" in exc.message
    else:
        raise AssertionError("juda katta fayl qabul qilinmadi")


def test_tiny_image_is_rejected() -> None:
    try:
        render_variants(jpeg_bytes(size=(40, 40)))
    except ApiError as exc:
        assert exc.code == "validation_error"
    else:
        raise AssertionError("juda kichik rasm qabul qilinmadi")
