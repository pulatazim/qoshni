"""Katalog o'qish sxemalari."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name_uz: str
    name_ru: str


class DistrictRead(BaseModel):
    id: int
    name_uz: str
    name_ru: str
    latitude: float
    longitude: float
