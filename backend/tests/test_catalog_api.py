"""Katalog endpointlari: kategoriyalar tartib bilan, tumanlar koordinata bilan."""

from __future__ import annotations

from app.models import Category, District
from app.modules.users.service import to_ewkt


async def test_categories_are_ordered_and_inactive_hidden(db_client, db_session) -> None:
    db_session.add_all(
        [
            Category(slug="mebel", name_uz="Mebellar", name_ru="Мебель", sort_order=2),
            Category(slug="kitob", name_uz="Kitoblar", name_ru="Книги", sort_order=1),
            Category(
                slug="yashirin",
                name_uz="O'chirilgan",
                name_ru="Удалено",
                sort_order=3,
                is_active=False,
            ),
        ]
    )
    await db_session.commit()

    response = await db_client.get("/api/v1/categories")
    assert response.status_code == 200, response.text
    assert [item["slug"] for item in response.json()] == ["kitob", "mebel"]
    assert response.json()[0]["name_ru"] == "Книги"


async def test_districts_expose_center_coordinates(db_client, db_session) -> None:
    db_session.add(
        District(
            name_uz="Chilonzor",
            name_ru="Чиланзар",
            center=to_ewkt(41.280_45, 69.226_81),
        )
    )
    await db_session.commit()

    response = await db_client.get("/api/v1/districts")
    assert response.status_code == 200, response.text
    district = response.json()[0]
    assert district["name_uz"] == "Chilonzor"
    # geography ustuni bazada ST_Y/ST_X bilan ochiladi — front shu raqamlarni oladi.
    assert district["latitude"] == 41.28045
    assert district["longitude"] == 69.22681
