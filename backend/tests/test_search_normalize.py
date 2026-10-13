"""normalize() — kirill/lotin birlashtirish testlari."""

from __future__ import annotations

import pytest

from app.modules.listings.search import build_search_text, normalize


@pytest.mark.parametrize(
    ("cyrillic", "latin"),
    [
        ("китоб", "kitob"),
        ("маҳалла", "mahalla"),
        ("чиновник", "chinovnik"),
        ("шакари", "shakari"),
        ("ўғир", "o'g'ir"),
        ("қоғоз", "qogoz"),
        ("ёзув", "yozuv"),
        ("юлдуз", "yulduz"),
        ("яхши", "yaxshi"),
        ("насос", "nasos"),
        ("фақат", "faqat"),
        ("эълон", "e'lon".replace("'", "")),
    ],
)
def test_cyrillic_matches_latin(cyrillic: str, latin: str) -> None:
    assert normalize(cyrillic) == normalize(latin)


def test_apostrophe_variants_are_equal() -> None:
    for spelling in ("o'rtancha", "oʻrtancha", "oʼrtancha", "o`rtancha", "ortancha"):
        assert normalize(spelling) == "ortancha"


def test_case_and_whitespace_collapse() -> None:
    assert normalize("  KITTAK   DAN   ") == "kittak dan"
    assert normalize("") == ""
    assert normalize(None) == ""


def test_shch_and_ts_combinations() -> None:
    assert normalize("щука") == "shchuka"
    assert normalize("кц") == "kts"


def test_latin_uzbek_letters_pass_through() -> None:
    # Lotin yozuvidagi o'zbek harflari (g', o', sh, ch) buzilmasligi kerak.
    assert normalize("Chorsu tog' pastida") == "chorsu tog pastida"
    assert normalize("Shahrisabzlik") == "shahrisabzlik"


def test_search_text_combines_title_and_description() -> None:
    text = build_search_text("Bislopok  velosiped", "SARTUROV  holati yaxshi")
    assert text == "bislopok velosiped sarturov holati yaxshi"


def test_search_text_handles_missing_description() -> None:
    assert build_search_text("Китоб", "") == "kitob"
