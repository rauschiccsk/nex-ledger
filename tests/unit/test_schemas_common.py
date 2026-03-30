"""Unit testy pre common schemas."""

from pydantic import BaseModel

from app.schemas.common import PaginatedResponse


class DummyItem(BaseModel):
    """Test item pre PaginatedResponse."""

    id: int
    name: str


def test_paginated_response_creation():
    """Test vytvorenia PaginatedResponse."""
    items = [
        DummyItem(id=1, name="Item 1"),
        DummyItem(id=2, name="Item 2"),
    ]

    response = PaginatedResponse[DummyItem](
        items=items, total=10, skip=0, limit=100
    )

    assert len(response.items) == 2
    assert response.total == 10
    assert response.skip == 0
    assert response.limit == 100


def test_paginated_response_empty():
    """Test prázdnej PaginatedResponse."""
    response = PaginatedResponse[DummyItem](items=[], total=0, skip=0, limit=100)

    assert len(response.items) == 0
    assert response.total == 0


def test_paginated_response_json():
    """Test JSON serialization."""
    items = [DummyItem(id=1, name="Test")]
    response = PaginatedResponse[DummyItem](
        items=items, total=1, skip=0, limit=100
    )

    json_data = response.model_dump()
    assert "items" in json_data
    assert "total" in json_data
    assert json_data["total"] == 1
