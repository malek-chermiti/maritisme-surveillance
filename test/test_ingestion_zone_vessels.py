from unittest.mock import MagicMock

from services.ingestion.service import get_vessels_in_zone


def test_get_vessels_in_zone_filters_by_bounds():
    vessel = MagicMock(
        mmsi=123456789,
        latitude=35.2,
        longitude=9.8,
        speed=12.5,
        heading=42.0,
        recorded_at="2024-01-01T00:00:00",
    )

    db = MagicMock()
    db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [vessel]

    results = get_vessels_in_zone(db, 32.0, 38.0, 7.5, 12.0)

    assert results == [vessel]
    assert len(results) == 1
    assert results[0].mmsi == 123456789
