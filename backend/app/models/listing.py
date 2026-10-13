"""E'lon va e'lon rasmlari. Lenta, qidiruv va masofa filtri shu jadval ustida ishlaydi."""

from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

# Holatlar (dizayn hujjati): active | reserved | sold | hidden | removed
STATUS_ACTIVE = "active"
STATUS_RESERVED = "reserved"
STATUS_SOLD = "sold"
STATUS_HIDDEN = "hidden"
STATUS_REMOVED = "removed"
LISTING_STATUSES = {STATUS_ACTIVE, STATUS_RESERVED, STATUS_SOLD, STATUS_HIDDEN, STATUS_REMOVED}

# Moderatsiya holati: auto_ok | pending | approved | rejected
MODERATION_STATES = {"auto_ok", "pending", "approved", "rejected"}


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        # Masofa filtri (ST_DWithin) uchun.
        Index("ix_listings_location", "location", postgresql_using="gist"),
        # Trigram qidiruv: kirill/lotin normalizatsiyadan o'tgan matn bo'yicha.
        Index(
            "ix_listings_search",
            "search_text",
            postgresql_ops={"search_text": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
        # Lenta saralashi uchun qisman indeks — o'chirilganlar kirmaydi.
        Index(
            "ix_listings_feed",
            "status",
            text("bumped_at DESC"),
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    seller_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False, server_default="")

    # So'mda; 0 = "bepul" (price_type=free) yoki "kelishib" (negotiable).
    price: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    # fixed | negotiable | free
    price_type: Mapped[str] = mapped_column(Text, nullable=False)
    # new | used
    condition: Mapped[str] = mapped_column(Text, nullable=False)

    # Xiralashtirilgan nuqta (~300 m); aniq manzil saqlanmaydi.
    location: Mapped[str] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False
    )
    district_id: Mapped[int | None] = mapped_column(ForeignKey("districts.id"), index=True)

    # title + description, normalize() qilingan matn — qidiruv shu ustunga qarab ishlaydi.
    search_text: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=STATUS_ACTIVE)
    moderation: Mapped[str] = mapped_column(Text, nullable=False, server_default="auto_ok")

    view_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    bumped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    images: Mapped[list["ListingImage"]] = relationship(
        cascade="all, delete-orphan", order_by="ListingImage.position", lazy="selectin"
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class ListingImage(Base):
    __tablename__ = "listing_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # R2'dagi kalit (masalan: listings/2026/10/abcd1234.webp)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    # 0 = muqova rasmi
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
