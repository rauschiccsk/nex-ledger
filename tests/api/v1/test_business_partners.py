"""
Tests for BusinessPartner CRUD endpoints — /api/v1/business-partners.

Uses TestClient with DB session override for transactional isolation.
24 tests across 5 endpoint groups.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.models.business_partner import BusinessPartner

BASE_URL = "/api/v1/business-partners"


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
def sample_partner(db_session: Session) -> BusinessPartner:
    """Insert a single business partner into the test DB."""
    p = BusinessPartner(
        partner_type="CUSTOMER",
        code="CUST001",
        name="Test Customer s.r.o.",
        tax_id="12345678",
        vat_number="SK2012345678",
        address="Hlavná 1, Bratislava",
        contact_person="Ján Novák",
        email="jan@test.sk",
        phone="+421900000001",
        is_active=True,
    )
    db_session.add(p)
    db_session.flush()
    return p


@pytest.fixture()
def multiple_partners(db_session: Session) -> list[BusinessPartner]:
    """Insert 5 business partners for pagination tests."""
    partners = []
    for i in range(1, 6):
        p = BusinessPartner(
            partner_type="CUSTOMER",
            code=f"CUST{i:03d}",
            name=f"Customer {i}",
            tax_id=f"TAX{i:05d}",
        )
        db_session.add(p)
        db_session.flush()
        partners.append(p)
    return partners


def _create_payload(**overrides) -> dict:
    """Helper to generate a valid create payload with optional overrides."""
    data = {
        "partner_type": "CUSTOMER",
        "code": "NEW001",
        "name": "New Partner s.r.o.",
        "tax_id": "99999999",
        "vat_number": "SK2099999999",
        "address": "Nová 42, Košice",
        "contact_person": "Peter Horváth",
        "email": "peter@newpartner.sk",
        "phone": "+421900111222",
        "is_active": True,
    }
    data.update(overrides)
    return data


# ===========================================================================
# GET /api/v1/business-partners — List (paginated)
# ===========================================================================


class TestListBusinessPartners:
    """Tests for GET /api/v1/business-partners."""

    def test_list_business_partners_empty(self, client: TestClient):
        """Empty database returns empty items list with zero total."""
        resp = client.get(BASE_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["skip"] == 0
        assert data["limit"] == 100

    def test_list_business_partners_with_items(
        self, client: TestClient, multiple_partners: list[BusinessPartner]
    ):
        """Returns all business partners with correct total."""
        resp = client.get(BASE_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    def test_list_business_partners_pagination_skip(
        self, client: TestClient, multiple_partners: list[BusinessPartner]
    ):
        """Skip parameter offsets results."""
        resp = client.get(f"{BASE_URL}?skip=3")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["skip"] == 3

    def test_list_business_partners_pagination_limit(
        self, client: TestClient, multiple_partners: list[BusinessPartner]
    ):
        """Limit parameter caps result count."""
        resp = client.get(f"{BASE_URL}?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["limit"] == 2

    def test_list_business_partners_pagination_skip_and_limit(
        self, client: TestClient, multiple_partners: list[BusinessPartner]
    ):
        """Combined skip and limit return correct slice."""
        resp = client.get(f"{BASE_URL}?skip=1&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["skip"] == 1
        assert data["limit"] == 2

    def test_list_business_partners_ordered_by_partner_id_asc(
        self, client: TestClient, multiple_partners: list[BusinessPartner]
    ):
        """Items are ordered by partner_id ASC (service default)."""
        resp = client.get(BASE_URL)
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["partner_id"] for item in data["items"]]
        assert ids == sorted(ids)

    def test_list_business_partners_default_pagination(
        self, client: TestClient, sample_partner: BusinessPartner
    ):
        """Default skip=0, limit=100 when no query params provided."""
        resp = client.get(BASE_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["skip"] == 0
        assert data["limit"] == 100
        assert data["total"] == 1
        assert len(data["items"]) == 1


# ===========================================================================
# GET /api/v1/business-partners/{partner_id} — Read one
# ===========================================================================


class TestGetBusinessPartner:
    """Tests for GET /api/v1/business-partners/{partner_id}."""

    def test_get_business_partner_success(
        self, client: TestClient, sample_partner: BusinessPartner
    ):
        """Successfully retrieve an existing partner."""
        resp = client.get(f"{BASE_URL}/{sample_partner.partner_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["partner_id"] == sample_partner.partner_id
        assert data["name"] == sample_partner.name

    def test_get_business_partner_not_found(self, client: TestClient):
        """Returns 404 for non-existent partner_id."""
        resp = client.get(f"{BASE_URL}/999999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_get_business_partner_returns_all_fields(
        self, client: TestClient, sample_partner: BusinessPartner
    ):
        """Response contains all expected fields from BusinessPartnerRead."""
        resp = client.get(f"{BASE_URL}/{sample_partner.partner_id}")
        assert resp.status_code == 200
        data = resp.json()
        expected_fields = {
            "partner_id",
            "partner_type",
            "code",
            "name",
            "tax_id",
            "vat_number",
            "address",
            "contact_person",
            "email",
            "phone",
            "is_active",
        }
        assert set(data.keys()) == expected_fields
        # Verify actual values
        assert data["partner_type"] == "CUSTOMER"
        assert data["code"] == "CUST001"
        assert data["tax_id"] == "12345678"
        assert data["vat_number"] == "SK2012345678"
        assert data["address"] == "Hlavná 1, Bratislava"
        assert data["contact_person"] == "Ján Novák"
        assert data["email"] == "jan@test.sk"
        assert data["phone"] == "+421900000001"
        assert data["is_active"] is True


# ===========================================================================
# POST /api/v1/business-partners — Create
# ===========================================================================


class TestCreateBusinessPartner:
    """Tests for POST /api/v1/business-partners."""

    def test_create_business_partner_success(self, client: TestClient):
        """Successfully create a new business partner."""
        payload = _create_payload()
        resp = client.post(BASE_URL, json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == payload["name"]
        assert data["code"] == payload["code"]
        assert "partner_id" in data

    def test_create_business_partner_returns_all_fields(self, client: TestClient):
        """Created partner response contains all expected fields."""
        payload = _create_payload()
        resp = client.post(BASE_URL, json=payload)
        assert resp.status_code == 201
        data = resp.json()
        expected_fields = {
            "partner_id",
            "partner_type",
            "code",
            "name",
            "tax_id",
            "vat_number",
            "address",
            "contact_person",
            "email",
            "phone",
            "is_active",
        }
        assert set(data.keys()) == expected_fields
        assert data["partner_type"] == "CUSTOMER"
        assert data["tax_id"] == "99999999"
        assert data["is_active"] is True

    def test_create_business_partner_duplicate_registration_number(
        self, client: TestClient, sample_partner: BusinessPartner
    ):
        """Returns 409 when code (registration_number) already exists."""
        payload = _create_payload(code=sample_partner.code)
        resp = client.post(BASE_URL, json=payload)
        assert resp.status_code == 409
        assert "code" in resp.json()["detail"].lower()

    def test_create_business_partner_duplicate_tax_number(
        self, client: TestClient, sample_partner: BusinessPartner
    ):
        """Returns 409 when tax_id (tax_number) already exists."""
        payload = _create_payload(code="UNIQUE001", tax_id=sample_partner.tax_id)
        resp = client.post(BASE_URL, json=payload)
        assert resp.status_code == 409
        assert "tax_id" in resp.json()["detail"].lower()

    def test_create_business_partner_missing_required_fields(
        self, client: TestClient
    ):
        """Returns 422 when required fields are missing."""
        # partner_type and name are required
        resp = client.post(BASE_URL, json={})
        assert resp.status_code == 422

    def test_create_business_partner_invalid_email(self, client: TestClient):
        """Returns 422 when email format is invalid."""
        payload = _create_payload(email="not-an-email")
        resp = client.post(BASE_URL, json=payload)
        assert resp.status_code == 422


# ===========================================================================
# PUT /api/v1/business-partners/{partner_id} — Update
# ===========================================================================


class TestUpdateBusinessPartner:
    """Tests for PUT /api/v1/business-partners/{partner_id}."""

    def test_update_business_partner_success(
        self, client: TestClient, sample_partner: BusinessPartner
    ):
        """Successfully update an existing partner."""
        resp = client.put(
            f"{BASE_URL}/{sample_partner.partner_id}",
            json={"name": "Updated Name s.r.o."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Name s.r.o."
        # Unchanged fields remain
        assert data["code"] == sample_partner.code

    def test_update_business_partner_not_found(self, client: TestClient):
        """Returns 404 for non-existent partner_id."""
        resp = client.put(
            f"{BASE_URL}/999999",
            json={"name": "Ghost Partner"},
        )
        assert resp.status_code == 404

    def test_update_business_partner_duplicate_registration_number(
        self,
        client: TestClient,
        db_session: Session,
        sample_partner: BusinessPartner,
    ):
        """Returns 409 when updating code to one that already exists."""
        # Create a second partner
        other = BusinessPartner(
            partner_type="SUPPLIER",
            code="SUP001",
            name="Supplier One",
        )
        db_session.add(other)
        db_session.flush()

        resp = client.put(
            f"{BASE_URL}/{other.partner_id}",
            json={"code": sample_partner.code},
        )
        assert resp.status_code == 409
        assert "code" in resp.json()["detail"].lower()

    def test_update_business_partner_duplicate_tax_number(
        self,
        client: TestClient,
        db_session: Session,
        sample_partner: BusinessPartner,
    ):
        """Returns 409 when updating tax_id to one that already exists."""
        other = BusinessPartner(
            partner_type="SUPPLIER",
            code="SUP002",
            name="Supplier Two",
            tax_id="UNIQUE_TAX",
        )
        db_session.add(other)
        db_session.flush()

        resp = client.put(
            f"{BASE_URL}/{other.partner_id}",
            json={"tax_id": sample_partner.tax_id},
        )
        assert resp.status_code == 409
        assert "tax_id" in resp.json()["detail"].lower()

    def test_update_business_partner_same_registration_number_ok(
        self, client: TestClient, sample_partner: BusinessPartner
    ):
        """Updating with the same code (own code) should NOT trigger 409."""
        resp = client.put(
            f"{BASE_URL}/{sample_partner.partner_id}",
            json={"code": sample_partner.code, "name": "Same Code OK"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == sample_partner.code
        assert resp.json()["name"] == "Same Code OK"

    def test_update_business_partner_partial_update(
        self, client: TestClient, sample_partner: BusinessPartner
    ):
        """Partial update changes only specified fields."""
        original_email = sample_partner.email
        resp = client.put(
            f"{BASE_URL}/{sample_partner.partner_id}",
            json={"phone": "+421911222333"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["phone"] == "+421911222333"
        assert data["email"] == original_email  # unchanged


# ===========================================================================
# DELETE /api/v1/business-partners/{partner_id} — Delete
# ===========================================================================


class TestDeleteBusinessPartner:
    """Tests for DELETE /api/v1/business-partners/{partner_id}."""

    def test_delete_business_partner_success(
        self, client: TestClient, sample_partner: BusinessPartner
    ):
        """Successfully delete an existing partner returns 204."""
        resp = client.delete(f"{BASE_URL}/{sample_partner.partner_id}")
        assert resp.status_code == 204
        assert resp.content == b""

        # Verify partner is gone
        resp2 = client.get(f"{BASE_URL}/{sample_partner.partner_id}")
        assert resp2.status_code == 404

    def test_delete_business_partner_not_found(self, client: TestClient):
        """Returns 404 for non-existent partner_id."""
        resp = client.delete(f"{BASE_URL}/999999")
        assert resp.status_code == 404
