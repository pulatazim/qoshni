"""blur_point — koordinata xiralashtirish (bazasiz unit test)."""

from __future__ import annotations

import math

from app.modules.users.service import BLUR_METERS, blur_point, to_ewkt

TASHKENT = (41.3123456, 69.2786543)


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine — tekshiruv uchun yetarli aniqlik."""
    radius = 6_371_000.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def test_blurred_point_is_within_about_300_m() -> None:
    lat, lon = blur_point(*TASHKENT)
    assert _distance_m(*TASHKENT, lat, lon) <= BLUR_METERS * 1.5


def test_point_inside_a_cell_maps_to_that_cell_center() -> None:
    base = blur_point(*TASHKENT)
    # Katak yarmi ~135 m; 45 m shimolga surgan nuqta shu katakda qoladi.
    inside = (base[0] + 0.0004, base[1])
    assert blur_point(*inside) == base


def test_far_points_stay_far() -> None:
    a = blur_point(41.3123456, 69.2786543)
    b = blur_point(41.3223456, 69.2786543)  # ~1.1 km shimol
    assert a != b
    assert _distance_m(*a, *b) > 800


def test_ewkt_format_and_longitude_first() -> None:
    assert to_ewkt(41.31, 69.27) == "SRID=4326;POINT(69.270000 41.310000)"


def test_longitude_grid_is_coarser_at_high_latitude() -> None:
    # Uzunlik qadami shirota bilan kengayadi: 0° da ~0.0027°, 70° da ~0.0079°.
    assert blur_point(0.0, 0.001)[1] != blur_point(0.0, 0.003)[1]
    assert blur_point(70.0, 0.001)[1] == blur_point(70.0, 0.003)[1]
