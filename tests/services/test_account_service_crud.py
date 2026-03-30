"""
Tests for AccountService CRUD operations.

Covers: list_accounts, get_account, create_account, update_account, delete_account.
"""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.account_type import AccountType
from app.models.chart_of_accounts import ChartOfAccounts
from app.models.currency import Currency
from app.models.import_batch import ImportBatch
from app.models.journal_entry import JournalEntry
from app.models.journal_entry_line import JournalEntryLine
from app.services.account_service import AccountService

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture()
def currency(db_session: Session) -> Currency:
    """Create EUR currency."""
    cur = Currency(currency_code="EUR", name="Euro", symbol="€")
    db_session.add(cur)
    db_session.flush()
    return cur


@pytest.fixture()
def account_type(db_session: Session) -> AccountType:
    """Create ASSET account type."""
    at = AccountType(code="ASSET", name="Assets")
    db_session.add(at)
    db_session.flush()
    return at


@pytest.fixture()
def chart(db_session: Session) -> ChartOfAccounts:
    """Create a chart of accounts."""
    coa = ChartOfAccounts(code="SK-2025", name="Slovak Chart 2025")
    db_session.add(coa)
    db_session.flush()
    return coa


@pytest.fixture()
def base_account_data(
    chart: ChartOfAccounts, account_type: AccountType, currency: Currency
) -> dict:
    """Base account data dict for creating accounts."""
    return {
        "chart_id": chart.chart_id,
        "account_number": "100",
        "name": "Cash",
        "account_type_id": account_type.account_type_id,
        "currency_code": currency.currency_code,
        "level": 1,
    }


@pytest.fixture()
def sample_account(db_session: Session, base_account_data: dict) -> Account:
    """Create a single account via the service."""
    return AccountService.create_account(db_session, base_account_data)


@pytest.fixture()
def multiple_accounts(
    db_session: Session,
    chart: ChartOfAccounts,
    account_type: AccountType,
    currency: Currency,
) -> list[Account]:
    """Create 5 accounts for pagination testing."""
    accounts = []
    for i in range(5):
        data = {
            "chart_id": chart.chart_id,
            "account_number": f"{(i + 1) * 100:03d}",
            "name": f"Account {i + 1}",
            "account_type_id": account_type.account_type_id,
            "currency_code": currency.currency_code,
            "level": 1,
        }
        acc = AccountService.create_account(db_session, data)
        accounts.append(acc)
    return accounts


# ── list_accounts Tests ──────────────────────────────────────────


class TestListAccounts:
    """Tests for AccountService.list_accounts()."""

    def test_list_accounts_empty(self, db_session: Session):
        """Empty database returns empty list and zero count."""
        accounts, total = AccountService.list_accounts(db_session)

        assert accounts == []
        assert total == 0

    def test_list_accounts_pagination(
        self, db_session: Session, multiple_accounts: list[Account]
    ):
        """Skip/limit pagination returns correct subset."""
        accounts, total = AccountService.list_accounts(
            db_session, skip=2, limit=2
        )

        assert len(accounts) == 2
        assert total == 5

    def test_list_accounts_ordering(
        self, db_session: Session, multiple_accounts: list[Account]
    ):
        """Accounts are ordered by account_number ASC."""
        accounts, total = AccountService.list_accounts(db_session)

        assert total == 5
        assert len(accounts) == 5

        # account_numbers should be in ascending order
        numbers = [a.account_number for a in accounts]
        assert numbers == sorted(numbers)


# ── get_account Tests ────────────────────────────────────────────


class TestGetAccount:
    """Tests for AccountService.get_account()."""

    def test_get_account_success(
        self, db_session: Session, sample_account: Account
    ):
        """Existing account is returned correctly."""
        result = AccountService.get_account(
            db_session, sample_account.account_id
        )

        assert result.account_id == sample_account.account_id
        assert result.name == "Cash"
        assert result.account_number == "100"

    def test_get_account_not_found(self, db_session: Session):
        """Non-existent account raises ValueError."""
        with pytest.raises(ValueError, match="Account 99999 not found"):
            AccountService.get_account(db_session, 99999)


# ── create_account Tests ─────────────────────────────────────────


class TestCreateAccount:
    """Tests for AccountService.create_account()."""

    def test_create_account_success(
        self, db_session: Session, base_account_data: dict
    ):
        """Account is created with required fields."""
        account = AccountService.create_account(db_session, base_account_data)

        assert account.account_id is not None
        assert account.account_number == "100"
        assert account.name == "Cash"
        assert account.level == 1

    def test_create_account_with_parent(
        self, db_session: Session, base_account_data: dict
    ):
        """Account is created with a valid parent reference."""
        # Create parent first
        parent = AccountService.create_account(db_session, base_account_data)

        # Create child
        child_data = {
            **base_account_data,
            "account_number": "101",
            "name": "Petty Cash",
            "parent_account_id": parent.account_id,
            "level": 2,
        }
        child = AccountService.create_account(db_session, child_data)

        assert child.parent_account_id == parent.account_id
        assert child.level == 2

    def test_create_account_parent_not_found(
        self, db_session: Session, base_account_data: dict
    ):
        """ValueError when parent_account_id references non-existent account."""
        base_account_data["parent_account_id"] = 99999

        with pytest.raises(ValueError, match="Account 99999 not found"):
            AccountService.create_account(db_session, base_account_data)


# ── update_account Tests ─────────────────────────────────────────


class TestUpdateAccount:
    """Tests for AccountService.update_account()."""

    def test_update_account_rename(
        self, db_session: Session, sample_account: Account
    ):
        """Account name can be updated."""
        updated = AccountService.update_account(
            db_session,
            sample_account.account_id,
            {"name": "Cash in Bank"},
        )

        assert updated.name == "Cash in Bank"
        assert updated.account_id == sample_account.account_id

    def test_update_account_change_parent(
        self,
        db_session: Session,
        sample_account: Account,
        base_account_data: dict,
    ):
        """Account parent can be changed to another existing account."""
        # Create a new parent
        new_parent_data = {
            **base_account_data,
            "account_number": "200",
            "name": "Bank Accounts",
        }
        new_parent = AccountService.create_account(db_session, new_parent_data)

        updated = AccountService.update_account(
            db_session,
            sample_account.account_id,
            {"parent_account_id": new_parent.account_id, "level": 2},
        )

        assert updated.parent_account_id == new_parent.account_id

    def test_update_account_not_found(self, db_session: Session):
        """Non-existent account raises ValueError."""
        with pytest.raises(ValueError, match="Account 99999 not found"):
            AccountService.update_account(
                db_session, 99999, {"name": "Ghost"}
            )

    def test_update_account_self_parent(
        self, db_session: Session, sample_account: Account
    ):
        """Setting account as its own parent raises ValueError."""
        with pytest.raises(ValueError, match="as its own parent"):
            AccountService.update_account(
                db_session,
                sample_account.account_id,
                {"parent_account_id": sample_account.account_id},
            )

    def test_update_account_circular_reference(
        self,
        db_session: Session,
        sample_account: Account,
        base_account_data: dict,
    ):
        """Setting parent to a child creates circular reference → ValueError."""
        # Create child of sample_account
        child_data = {
            **base_account_data,
            "account_number": "101",
            "name": "Child Account",
            "parent_account_id": sample_account.account_id,
            "level": 2,
        }
        child = AccountService.create_account(db_session, child_data)

        # Create grandchild
        grandchild_data = {
            **base_account_data,
            "account_number": "102",
            "name": "Grandchild Account",
            "parent_account_id": child.account_id,
            "level": 3,
        }
        grandchild = AccountService.create_account(db_session, grandchild_data)

        # Try to set sample_account's parent to grandchild → circular
        with pytest.raises(ValueError, match="circular reference"):
            AccountService.update_account(
                db_session,
                sample_account.account_id,
                {"parent_account_id": grandchild.account_id},
            )


# ── delete_account Tests ─────────────────────────────────────────


class TestDeleteAccount:
    """Tests for AccountService.delete_account()."""

    def test_delete_account_success(
        self, db_session: Session, sample_account: Account
    ):
        """Account without children and zero balance is deleted."""
        account_id = sample_account.account_id
        AccountService.delete_account(db_session, account_id)

        # Verify account no longer exists
        result = db_session.execute(
            select(Account).where(Account.account_id == account_id)
        ).scalar_one_or_none()
        assert result is None

    def test_delete_account_has_children(
        self,
        db_session: Session,
        sample_account: Account,
        base_account_data: dict,
    ):
        """Account with child accounts cannot be deleted."""
        # Create a child account
        child_data = {
            **base_account_data,
            "account_number": "101",
            "name": "Child",
            "parent_account_id": sample_account.account_id,
            "level": 2,
        }
        AccountService.create_account(db_session, child_data)

        with pytest.raises(ValueError, match="has 1 child accounts"):
            AccountService.delete_account(
                db_session, sample_account.account_id
            )

    def test_delete_account_nonzero_balance(
        self,
        db_session: Session,
        sample_account: Account,
        chart: ChartOfAccounts,
        account_type: AccountType,
        currency: Currency,
    ):
        """Account with non-zero balance cannot be deleted."""
        # Create journal entry infrastructure
        batch = ImportBatch(
            filename="test.csv",
            file_hash="b" * 64,
            status="imported",
        )
        db_session.add(batch)
        db_session.flush()

        entry = JournalEntry(
            batch_id=batch.batch_id,
            entry_number="JE-001",
            entry_date=date(2025, 1, 1),
            description="Test entry",
        )
        db_session.add(entry)
        db_session.flush()

        # Create a line with debit on sample_account
        line = JournalEntryLine(
            entry_id=entry.entry_id,
            line_number=1,
            account_id=sample_account.account_id,
            debit_amount=Decimal("1000.00"),
            credit_amount=Decimal("0.00"),
            currency_code=currency.currency_code,
        )
        db_session.add(line)
        db_session.flush()

        with pytest.raises(ValueError, match="balance is"):
            AccountService.delete_account(
                db_session, sample_account.account_id
            )

    def test_delete_account_not_found(self, db_session: Session):
        """Non-existent account raises ValueError."""
        with pytest.raises(ValueError, match="Account 99999 not found"):
            AccountService.delete_account(db_session, 99999)
