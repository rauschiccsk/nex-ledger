"""
Tests for AccountType CRUD endpoints — /api/v1/account-types.

Uses TestClient with DB session override for transactional isolation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.models.account_type import AccountType

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
def sample_account_type(db_session: Session) -> AccountType:
    """Insert a sample account type into the test DB."""
    at = AccountType(code="ASSET", name="Assets", description="Asset accounts")
    db_session.add(at)
    db_session.flush()
    return at


@pytest.fixture()
def multiple_account_types(db_session: Session) -> list[AccountType]:
    """Insert 5 account types for pagination tests."""
    types = [
        AccountType(code="ASSET", name="Assets"),
        AccountType(code="LIAB", name="Liabilities"),
        AccountType(code="EQUITY", name="Equity"),
        AccountType(code="REV", name="Revenue"),
        AccountType(code="EXP", name="Expenses"),
    ]
    for t in types:
        db_session.add(t)
    db_session.flush()
    return types


# ---------------------------------------------------------------------------
# GET /api/v1/account-types — List (paginated)
# ---------------------------------------------------------------------------


class TestListAccountTypes:
    """Tests for GET /api/v1/account-types."""

    def test_list_empty(self, client: TestClient):
        """Empty database returns empty items list."""
        resp = client.get("/api/v1/account-types")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["skip"] == 0
        assert data["limit"] == 100

    def test_list_returns_items(
        self, client: TestClient, multiple_account_types: list[AccountType]
    ):
        """Returns all account types with correct total."""
        resp = client.get("/api/v1/account-types")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    def test_list_pagination_skip(
        self, client: TestClient, multiple_account_types: list[AccountType]
    ):
        """Skip parameter offsets results."""
        resp = client.get("/api/v1/account-types?skip=3")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["skip"] == 3

    def test_list_pagination_limit(
        self, client: TestClient, multiple_account_types: list[AccountType]
    ):
        """Limit parameter caps result count."""
        resp = client.get("/api/v1/account-types?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["limit"] == 2

    def test_list_pagination_skip_and_limit(
        self, client: TestClient, multiple_account_types: list[AccountType]
    ):
        """Combined skip + limit."""
        resp = client.get("/api/v1/account-types?skip=2&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2


# ---------------------------------------------------------------------------
# GET /api/v1/account-types/{id} — Read one
# ---------------------------------------------------------------------------


class TestGetAccountType:
    """Tests for GET /api/v1/account-types/{id}."""

    def test_get_existing(
        self, client: TestClient, sample_account_type: AccountType
    ):
        """Returns account type by ID."""
        resp = client.get(
            f"/api/v1/account-types/{sample_account_type.account_type_id}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "ASSET"
        assert data["name"] == "Assets"
        assert data["description"] == "Asset accounts"
        assert data["account_type_id"] == sample_account_type.account_type_id

    def test_get_not_found(self, client: TestClient):
        """Returns 404 for non-existent ID."""
        resp = client.get("/api/v1/account-types/99999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# POST /api/v1/account-types — Create
# ---------------------------------------------------------------------------


class TestCreateAccountType:
    """Tests for POST /api/v1/account-types."""

    def test_create_success(self, client: TestClient):
        """Creates account type and returns 201."""
        payload = {
            "code": "ASSET",
            "name": "Assets",
            "description": "All asset accounts",
        }
        resp = client.post("/api/v1/account-types", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == "ASSET"
        assert data["name"] == "Assets"
        assert data["description"] == "All asset accounts"
        assert "account_type_id" in data

    def test_create_minimal(self, client: TestClient):
        """Creates account type without optional description."""
        payload = {"code": "LIAB", "name": "Liabilities"}
        resp = client.post("/api/v1/account-types", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == "LIAB"
        assert data["description"] is None

    def test_create_duplicate_code(
        self, client: TestClient, sample_account_type: AccountType
    ):
        """Returns 409 for duplicate code."""
        payload = {"code": "ASSET", "name": "Duplicate Assets"}
        resp = client.post("/api/v1/account-types", json=payload)
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"].lower()

    def test_create_empty_name(self, client: TestClient):
        """Returns 422 for empty name."""
        payload = {"code": "TEST", "name": ""}
        resp = client.post("/api/v1/account-types", json=payload)
        assert resp.status_code == 422

    def test_create_whitespace_name(self, client: TestClient):
        """Returns 422 for whitespace-only name."""
        payload = {"code": "TEST", "name": "   "}
        resp = client.post("/api/v1/account-types", json=payload)
        assert resp.status_code == 422

    def test_create_missing_code(self, client: TestClient):
        """Returns 422 when code is missing."""
        payload = {"name": "No Code Type"}
        resp = client.post("/api/v1/account-types", json=payload)
        assert resp.status_code == 422

    def test_create_missing_name(self, client: TestClient):
        """Returns 422 when name is missing."""
        payload = {"code": "NONAME"}
        resp = client.post("/api/v1/account-types", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/v1/account-types/{id} — Update
# ---------------------------------------------------------------------------


class TestUpdateAccountType:
    """Tests for PUT /api/v1/account-types/{id}."""

    def test_update_success(
        self, client: TestClient, sample_account_type: AccountType
    ):
        """Updates account type fields."""
        payload = {"name": "Updated Assets", "description": "Updated desc"}
        resp = client.put(
            f"/api/v1/account-types/{sample_account_type.account_type_id}",
            json=payload,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Assets"
        assert data["description"] == "Updated desc"
        # Code unchanged
        assert data["code"] == "ASSET"

    def test_update_code(
        self, client: TestClient, sample_account_type: AccountType
    ):
        """Updates code field."""
        payload = {"code": "AST"}
        resp = client.put(
            f"/api/v1/account-types/{sample_account_type.account_type_id}",
            json=payload,
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == "AST"

    def test_update_not_found(self, client: TestClient):
        """Returns 404 for non-existent ID."""
        payload = {"name": "Ghost"}
        resp = client.put("/api/v1/account-types/99999", json=payload)
        assert resp.status_code == 404

    def test_update_duplicate_code(
        self, client: TestClient, multiple_account_types: list[AccountType]
    ):
        """Returns 409 when updating code to existing code of another record."""
        # Try to set second type's code to first type's code
        second = multiple_account_types[1]
        payload = {"code": "ASSET"}  # code of first type
        resp = client.put(
            f"/api/v1/account-types/{second.account_type_id}",
            json=payload,
        )
        assert resp.status_code == 409

    def test_update_same_code_own_record(
        self, client: TestClient, sample_account_type: AccountType
    ):
        """Updating to own current code should succeed."""
        payload = {"code": "ASSET", "name": "Still Assets"}
        resp = client.put(
            f"/api/v1/account-types/{sample_account_type.account_type_id}",
            json=payload,
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == "ASSET"

    def test_update_empty_name(
        self, client: TestClient, sample_account_type: AccountType
    ):
        """Returns 422 when name is set to empty string."""
        payload = {"name": "   "}
        resp = client.put(
            f"/api/v1/account-types/{sample_account_type.account_type_id}",
            json=payload,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /api/v1/account-types/{id}
# ---------------------------------------------------------------------------


class TestDeleteAccountType:
    """Tests for DELETE /api/v1/account-types/{id}."""

    def test_delete_success(
        self, client: TestClient, sample_account_type: AccountType
    ):
        """Deletes account type and returns 204."""
        resp = client.delete(
            f"/api/v1/account-types/{sample_account_type.account_type_id}"
        )
        assert resp.status_code == 204
        assert resp.content == b""

        # Verify it's gone
        resp2 = client.get(
            f"/api/v1/account-types/{sample_account_type.account_type_id}"
        )
        assert resp2.status_code == 404

    def test_delete_not_found(self, client: TestClient):
        """Returns 404 for non-existent ID."""
        resp = client.delete("/api/v1/account-types/99999")
        assert resp.status_code == 404
