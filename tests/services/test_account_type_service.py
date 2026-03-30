"""
Tests for AccountTypeService CRUD operations.

Covers: list_account_types, get_account_type, create_account_type,
        update_account_type, delete_account_type.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.account_type import AccountType
from app.models.chart_of_accounts import ChartOfAccounts
from app.models.currency import Currency
from app.services.account_type_service import AccountTypeService

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture()
def asset_type(db_session: Session) -> AccountType:
    """Create ASSET account type."""
    at = AccountType(code="ASSET", name="Assets", description="Asset accounts")
    db_session.add(at)
    db_session.flush()
    return at


@pytest.fixture()
def liability_type(db_session: Session) -> AccountType:
    """Create LIABILITY account type."""
    at = AccountType(code="LIAB", name="Liabilities")
    db_session.add(at)
    db_session.flush()
    return at


@pytest.fixture()
def multiple_account_types(db_session: Session) -> list[AccountType]:
    """Create 5 account types for pagination testing."""
    types_data = [
        ("ASSET", "Assets"),
        ("LIAB", "Liabilities"),
        ("EQUITY", "Equity"),
        ("REV", "Revenue"),
        ("EXP", "Expenses"),
    ]
    account_types = []
    for code, name in types_data:
        at = AccountType(code=code, name=name)
        db_session.add(at)
        db_session.flush()
        account_types.append(at)
    return account_types


@pytest.fixture()
def account_with_type(
    db_session: Session, asset_type: AccountType
) -> Account:
    """Create an account referencing the ASSET account type."""
    # Currency
    cur = Currency(currency_code="EUR", name="Euro", symbol="€")
    db_session.add(cur)
    db_session.flush()

    # ChartOfAccounts
    coa = ChartOfAccounts(code="SK-2025", name="Slovak Chart 2025")
    db_session.add(coa)
    db_session.flush()

    # Account referencing asset_type
    account = Account(
        chart_id=coa.chart_id,
        account_number="100",
        name="Cash",
        account_type_id=asset_type.account_type_id,
        currency_code=cur.currency_code,
        level=1,
    )
    db_session.add(account)
    db_session.flush()
    return account


# ── list_account_types Tests ─────────────────────────────────────


class TestListAccountTypes:
    """Tests for AccountTypeService.list_account_types()."""

    def test_list_empty(self, db_session: Session):
        """Empty database returns empty list and zero count."""
        account_types, total = AccountTypeService.list_account_types(db_session)

        assert account_types == []
        assert total == 0

    def test_list_with_pagination(
        self, db_session: Session, multiple_account_types: list[AccountType]
    ):
        """Skip/limit pagination returns correct subset."""
        account_types, total = AccountTypeService.list_account_types(
            db_session, skip=2, limit=2
        )

        assert len(account_types) == 2
        assert total == 5

        # IDs are autoincrement — skip=2 returns 3rd and 4th inserted
        ids = [at.account_type_id for at in account_types]
        expected_ids = [
            multiple_account_types[2].account_type_id,
            multiple_account_types[3].account_type_id,
        ]
        assert ids == expected_ids

    def test_list_ordering(
        self, db_session: Session, multiple_account_types: list[AccountType]
    ):
        """Account types are ordered by account_type_id ASC."""
        account_types, total = AccountTypeService.list_account_types(db_session)

        assert total == 5
        assert len(account_types) == 5

        ids = [at.account_type_id for at in account_types]
        assert ids == sorted(ids)


# ── get_account_type Tests ───────────────────────────────────────


class TestGetAccountType:
    """Tests for AccountTypeService.get_account_type()."""

    def test_get_success(self, db_session: Session, asset_type: AccountType):
        """Existing account type is returned correctly."""
        result = AccountTypeService.get_account_type(
            db_session, asset_type.account_type_id
        )

        assert result.account_type_id == asset_type.account_type_id
        assert result.code == "ASSET"
        assert result.name == "Assets"
        assert result.description == "Asset accounts"

    def test_get_not_found(self, db_session: Session):
        """Non-existent account type raises ValueError."""
        with pytest.raises(ValueError, match="AccountType with ID 99999 not found"):
            AccountTypeService.get_account_type(db_session, 99999)


# ── create_account_type Tests ────────────────────────────────────


class TestCreateAccountType:
    """Tests for AccountTypeService.create_account_type()."""

    def test_create_success(self, db_session: Session):
        """Account type is created with required fields."""
        account_type = AccountTypeService.create_account_type(
            db_session,
            {
                "code": "ASSET",
                "name": "Assets",
                "description": "Asset accounts",
            },
        )

        assert account_type.code == "ASSET"
        assert account_type.name == "Assets"
        assert account_type.description == "Asset accounts"
        assert account_type.account_type_id is not None

        # Verify in DB
        result = db_session.execute(
            select(AccountType).where(
                AccountType.account_type_id == account_type.account_type_id
            )
        ).scalar_one_or_none()
        assert result is not None
        assert result.name == "Assets"

    def test_create_missing_name(self, db_session: Session):
        """Missing name raises ValueError."""
        with pytest.raises(ValueError, match="Account type name is required"):
            AccountTypeService.create_account_type(
                db_session,
                {"code": "ASSET"},
            )


# ── update_account_type Tests ────────────────────────────────────


class TestUpdateAccountType:
    """Tests for AccountTypeService.update_account_type()."""

    def test_update_success(self, db_session: Session, asset_type: AccountType):
        """Account type name and description can be updated."""
        updated = AccountTypeService.update_account_type(
            db_session,
            asset_type.account_type_id,
            {"name": "Updated Assets", "description": "Updated description"},
        )

        assert updated.name == "Updated Assets"
        assert updated.description == "Updated description"
        assert updated.code == "ASSET"

    def test_update_not_found(self, db_session: Session):
        """Non-existent account type raises ValueError."""
        with pytest.raises(ValueError, match="AccountType with ID 99999 not found"):
            AccountTypeService.update_account_type(
                db_session, 99999, {"name": "Ghost"}
            )


# ── delete_account_type Tests ────────────────────────────────────


class TestDeleteAccountType:
    """Tests for AccountTypeService.delete_account_type()."""

    def test_delete_success(self, db_session: Session, asset_type: AccountType):
        """Unused account type is deleted successfully."""
        type_id = asset_type.account_type_id
        AccountTypeService.delete_account_type(db_session, type_id)

        # Verify account type no longer exists
        result = db_session.execute(
            select(AccountType).where(AccountType.account_type_id == type_id)
        ).scalar_one_or_none()
        assert result is None

    def test_delete_in_use(
        self,
        db_session: Session,
        asset_type: AccountType,
        account_with_type: Account,
    ):
        """Account type referenced by accounts cannot be deleted."""
        with pytest.raises(
            ValueError,
            match=r"Cannot delete AccountType \d+: referenced by 1 accounts",
        ):
            AccountTypeService.delete_account_type(
                db_session, asset_type.account_type_id
            )

    def test_delete_not_found(self, db_session: Session):
        """Non-existent account type raises ValueError."""
        with pytest.raises(ValueError, match="AccountType with ID 99999 not found"):
            AccountTypeService.delete_account_type(db_session, 99999)
