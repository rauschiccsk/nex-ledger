"""
Tests for TaxRate CRUD endpoints — /api/v1/tax-rates.

Uses TestClient with DB session override for transactional isolation.
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.models.tax_rate import TaxRate

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(db_session: Session):
    """TestClient with get_db overridden to use test transaction session."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_tax_rate(db_session: Session) -> TaxRate:
    """Insert a sample VAT 20% tax rate into the test DB."""
    tr = TaxRate(code="VAT20", name="VAT 20%", rate=Decimal("20.00"))
    db_session.add(tr)
    db_session.flush()
    return tr


@pytest.fixture()
def multiple_tax_rates(db_session: Session) -> list[TaxRate]:
    """Insert 5 tax rates for pagination tests."""
    rates_data = [
        ("VAT20", "VAT 20%", Decimal("20.00")),
        ("VAT10", "VAT 10%", Decimal("10.00")),
        ("VAT0", "VAT 0%", Decimal("0.00")),
        ("ST5", "Sales Tax 5%", Decimal("5.00")),
        ("ST15", "Sales Tax 15%", Decimal("15.00")),
    ]
    tax_rates = []
    for code, name, rate in rates_data:
        tr = TaxRate(code=code, name=name, rate=rate)
        db_session.add(tr)
        db_session.flush()
        tax_rates.append(tr)
    return tax_rates


# ---------------------------------------------------------------------------
# GET /api/v1/tax-rates — List (paginated)
# ---------------------------------------------------------------------------


class TestListTaxRates:
    """Tests for GET /api/v1/tax-rates."""

    def test_list_empty(self, client: TestClient):
        """Empty database returns empty items list."""
        resp = client.get("/api/v1/tax-rates")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["skip"] == 0
        assert data["limit"] == 100

    def test_list_returns_items(
        self, client: TestClient, multiple_tax_rates: list[TaxRate]
    ):
        """Returns all tax rates with correct total."""
        resp = client.get("/api/v1/tax-rates")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    def test_list_pagination_skip(
        self, client: TestClient, multiple_tax_rates: list[TaxRate]
    ):
        """Skip parameter offsets results."""
        resp = client.get("/api/v1/tax-rates?skip=3")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["skip"] == 3

    def test_list_pagination_limit(
        self, client: TestClient, multiple_tax_rates: list[TaxRate]
    ):
        """Limit parameter caps result count."""
        resp = client.get("/api/v1/tax-rates?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["limit"] == 2

    def test_list_pagination_skip_and_limit(
        self, client: TestClient, multiple_tax_rates: list[TaxRate]
    ):
        """Combined skip + limit."""
        resp = client.get("/api/v1/tax-rates?skip=2&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_list_order_by_id_asc(
        self, client: TestClient, multiple_tax_rates: list[TaxRate]
    ):
        """Tax rates are returned ordered by tax_rate_id ASC."""
        resp = client.get("/api/v1/tax-rates")
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["tax_rate_id"] for item in data["items"]]
        assert ids == sorted(ids)

    def test_list_default_skip_and_limit(self, client: TestClient):
        """Default query params are skip=0 and limit=100."""
        resp = client.get("/api/v1/tax-rates")
        assert resp.status_code == 200
        data = resp.json()
        assert data["skip"] == 0
        assert data["limit"] == 100


# ---------------------------------------------------------------------------
# GET /api/v1/tax-rates/{id} — Read one
# ---------------------------------------------------------------------------


class TestGetTaxRate:
    """Tests for GET /api/v1/tax-rates/{id}."""

    def test_get_existing(
        self, client: TestClient, sample_tax_rate: TaxRate
    ):
        """Returns tax rate by ID."""
        resp = client.get(
            f"/api/v1/tax-rates/{sample_tax_rate.tax_rate_id}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "VAT20"
        assert data["name"] == "VAT 20%"
        assert data["tax_rate_id"] == sample_tax_rate.tax_rate_id

    def test_get_not_found(self, client: TestClient):
        """Returns 404 for non-existent ID."""
        resp = client.get("/api/v1/tax-rates/99999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_get_returns_all_fields(
        self, client: TestClient, sample_tax_rate: TaxRate
    ):
        """Response includes all expected fields from TaxRateRead schema."""
        resp = client.get(
            f"/api/v1/tax-rates/{sample_tax_rate.tax_rate_id}"
        )
        assert resp.status_code == 200
        data = resp.json()
        expected_keys = {
            "tax_rate_id",
            "code",
            "name",
            "rate",
            "valid_from",
            "valid_to",
            "is_active",
        }
        assert set(data.keys()) == expected_keys


# ---------------------------------------------------------------------------
# POST /api/v1/tax-rates — Create
# ---------------------------------------------------------------------------


class TestCreateTaxRate:
    """Tests for POST /api/v1/tax-rates."""

    def test_create_success(self, client: TestClient):
        """Creates tax rate and returns 201."""
        payload = {
            "code": "VAT20",
            "name": "VAT 20%",
            "rate": "20.00",
        }
        resp = client.post("/api/v1/tax-rates", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == "VAT20"
        assert data["name"] == "VAT 20%"
        assert "tax_rate_id" in data

    def test_create_with_all_fields(self, client: TestClient):
        """Creates tax rate with all optional fields."""
        payload = {
            "code": "VAT10",
            "name": "VAT 10%",
            "rate": "10.00",
            "valid_from": "2025-01-01",
            "valid_to": "2025-12-31",
            "is_active": False,
        }
        resp = client.post("/api/v1/tax-rates", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["valid_from"] == "2025-01-01"
        assert data["valid_to"] == "2025-12-31"
        assert data["is_active"] is False

    def test_create_duplicate_name(
        self, client: TestClient, sample_tax_rate: TaxRate
    ):
        """Returns 409 for duplicate name."""
        payload = {
            "code": "DUP",
            "name": "VAT 20%",
            "rate": "20.00",
        }
        resp = client.post("/api/v1/tax-rates", json=payload)
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"].lower()

    def test_create_missing_code(self, client: TestClient):
        """Returns 422 when code is missing."""
        payload = {"name": "No Code", "rate": "10.00"}
        resp = client.post("/api/v1/tax-rates", json=payload)
        assert resp.status_code == 422

    def test_create_missing_name(self, client: TestClient):
        """Returns 422 when name is missing."""
        payload = {"code": "NONAME", "rate": "10.00"}
        resp = client.post("/api/v1/tax-rates", json=payload)
        assert resp.status_code == 422

    def test_create_missing_rate(self, client: TestClient):
        """Returns 422 when rate is missing."""
        payload = {"code": "NORATE", "name": "No Rate"}
        resp = client.post("/api/v1/tax-rates", json=payload)
        assert resp.status_code == 422

    def test_create_rate_out_of_range(self, client: TestClient):
        """Returns 422 when rate exceeds 100."""
        payload = {"code": "BAD", "name": "Bad Rate", "rate": "101.00"}
        resp = client.post("/api/v1/tax-rates", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/v1/tax-rates/{id} — Update
# ---------------------------------------------------------------------------


class TestUpdateTaxRate:
    """Tests for PUT /api/v1/tax-rates/{id}."""

    def test_update_success(
        self, client: TestClient, sample_tax_rate: TaxRate
    ):
        """Updates tax rate fields."""
        payload = {"name": "Updated VAT", "rate": "21.00"}
        resp = client.put(
            f"/api/v1/tax-rates/{sample_tax_rate.tax_rate_id}",
            json=payload,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated VAT"
        # Code unchanged
        assert data["code"] == "VAT20"

    def test_update_not_found(self, client: TestClient):
        """Returns 404 for non-existent ID."""
        payload = {"name": "Ghost"}
        resp = client.put("/api/v1/tax-rates/99999", json=payload)
        assert resp.status_code == 404

    def test_update_duplicate_name(
        self, client: TestClient, multiple_tax_rates: list[TaxRate]
    ):
        """Returns 409 when updating name to existing name of another record."""
        second = multiple_tax_rates[1]
        payload = {"name": "VAT 20%"}  # name of first tax rate
        resp = client.put(
            f"/api/v1/tax-rates/{second.tax_rate_id}",
            json=payload,
        )
        assert resp.status_code == 409

    def test_update_same_name_own_record(
        self, client: TestClient, sample_tax_rate: TaxRate
    ):
        """Updating to own current name should succeed."""
        payload = {"name": "VAT 20%", "rate": "22.00"}
        resp = client.put(
            f"/api/v1/tax-rates/{sample_tax_rate.tax_rate_id}",
            json=payload,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "VAT 20%"

    def test_update_partial(
        self, client: TestClient, sample_tax_rate: TaxRate
    ):
        """Partial update only changes provided fields."""
        payload = {"is_active": False}
        resp = client.put(
            f"/api/v1/tax-rates/{sample_tax_rate.tax_rate_id}",
            json=payload,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_active"] is False
        assert data["name"] == "VAT 20%"
        assert data["code"] == "VAT20"


# ---------------------------------------------------------------------------
# DELETE /api/v1/tax-rates/{id}
# ---------------------------------------------------------------------------


class TestDeleteTaxRate:
    """Tests for DELETE /api/v1/tax-rates/{id}."""

    def test_delete_success(
        self, client: TestClient, sample_tax_rate: TaxRate
    ):
        """Deletes tax rate and returns 204."""
        resp = client.delete(
            f"/api/v1/tax-rates/{sample_tax_rate.tax_rate_id}"
        )
        assert resp.status_code == 204
        assert resp.content == b""

        # Verify it's gone
        resp2 = client.get(
            f"/api/v1/tax-rates/{sample_tax_rate.tax_rate_id}"
        )
        assert resp2.status_code == 404

    def test_delete_not_found(self, client: TestClient):
        """Returns 404 for non-existent ID."""
        resp = client.delete("/api/v1/tax-rates/99999")
        assert resp.status_code == 404
