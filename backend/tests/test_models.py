from geoalchemy2 import Geography

from app.core.db import Base
from app.models import District


def test_districts_registered() -> None:
    table = Base.metadata.tables["districts"]

    assert isinstance(table.c.center.type, Geography)
    assert table.c.center.type.srid == 4326
    assert not table.c.name_uz.nullable
    assert District.__tablename__ == "districts"
