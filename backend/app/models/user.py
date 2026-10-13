"""Foydalanuvchi profili. Telegram ID orqali topiladi, JWT esa shu jadvalning id'sini saqlaydi."""

from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)

    username: Mapped[str | None] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    # requestContact tugmasi orqali keladi, ixtiyoriy va hech qachon ommaga ko'rsatilmaydi.
    phone: Mapped[str | None] = mapped_column(Text)
    avatar_key: Mapped[str | None] = mapped_column(Text)

    # uz | ru
    language: Mapped[str] = mapped_column(Text, nullable=False, server_default="uz")

    district_id: Mapped[int | None] = mapped_column(ForeignKey("districts.id"))

    # Xiralashtirilgan (~300 m katak) uy nuqtasi; aniq koordinata saqlanmaydi.
    home_point: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False)
    )

    # trust_events jadvalidan hisoblanib keshlanadi (5-hafta).
    trust_score: Mapped[int] = mapped_column(nullable=False, server_default="50")

    # user | moderator | admin
    role: Mapped[str] = mapped_column(Text, nullable=False, server_default="user")
    # active | banned | deleted
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="active")

    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<User {self.id} tg={self.telegram_id} {self.display_name!r}>"
