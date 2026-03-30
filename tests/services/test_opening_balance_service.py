"""
Tests for OpeningBalanceService CRUD operations.

Covers: list_balances, get_balance, create_balance, update_balance, delete_balance.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.account_type import AccountType
from app.models.accounting_period import AccountingPeriod
from app.models.chart_of_accounts import ChartOfAccounts
from app.models.currency import Currency
from app.models.opening_balance import OpeningBalance
from app.services.opening_balance_service import OpeningBalanceService

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture()
def chart(db_session: Session) -> ChartOfAccounts:
    """Create chart of accounts."""
    coa = ChartOfAccounts(code="SK-2025", name="Slovak Chart 2025")
    db_session.add(coa)
    db_session.flush()
    return coa


@pytest.fixture()
def account_type(db_session: Session) -> AccountType:
    """Create account type."""
    at = AccountType(code="ASSET", name="Assets")
    db_session.add(at)
    db_session.flush()
    return at


@pytest.fixture()
def currency(db_session: Session) -> Currency:
    """Create EUR currency."""
    cur = Currency(currency_code="EUR", name="Euro", symbol="€")
    db_session.add(cur)
    db_session.flush()
    return cur


@pytest.fixture()
def account(
    db_session: Session,
    chart: ChartOfAccounts,
    account_type: AccountType,
    currency: Currency,
) -> Account:
    """Create an account for FK references."""
    acc = Account(
        chart_id=chart.chart_id,
        account_number="100",
        name="Cash",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        level=1,
    )
    db_session.add(acc)
    db_session.flush()
    return acc


@pytest.fixture()
def second_account(
    db_session: Session,
    chart: ChartOfAccounts,
    account_type: AccountType,
    currency: Currency,
) -> Account:
    """Create a second account for uniqueness tests."""
    acc = Account(
        chart_id=chart.chart_id,
        account_number="200",
        name="Bank",
        account_type_id=account_type.account_type_id,
        currency_code=currency.currency_code,
        level=1,
    )
    db_session.add(acc)
    db_session.flush()
    return acc


@pytest.fixture()
def period(db_session: Session, chart: ChartOfAccounts) -> AccountingPeriod:
    """Create an accounting period."""
    p = AccountingPeriod(
        chart_id=chart.chart_id,
        year=2025,
        period_number=1,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )
    db_session.add(p)
    db_session.flush()
    return p


@pytest.fixture()
def second_period(
    db_session: Session, chart: ChartOfAccounts
) -> AccountingPeriod:
    """Create a second accounting period for uniqueness tests."""
    p = AccountingPeriod(
        chart_id=chart.chart_id,
        year=2025,
        period_number=2,
        start_date=date(2025, 2, 1),
        end_date=date(2025, 2, 28),
    )
    db_session.add(p)
    db_session.flush()
    return p


@pytest.fixture()
def balance(
    db_session: Session, period: AccountingPeriod, account: Account
) -> OpeningBalance:
    """Create a single opening balance."""
    return OpeningBalanceService.create_balance(
        db_session,
        {
            "period_id": period.period_id,
            "account_id": account.account_id,
            "debit_amount": Decimal("1000.00"),
            "credit_amount": Decimal("0.00"),
        },
    )


@pytest.fixture()
def three_balances(
    db_session: Session,
    period: AccountingPeriod,
    second_period: AccountingPeriod,
    account: Account,
    second_account: Account,
) -> list[OpeningBalance]:
    """Create 3 opening balances for list/pagination testing."""
    balances = []
    combos = [
        (period.period_id, account.account_id),
        (period.period_id, second_account.account_id),
        (second_period.period_id, account.account_id),
    ]
    for pid, aid in combos:
        b = OpeningBalanceService.create_balance(
            db_session,
            {
                "period_id": pid,
                "account_id": aid,
                "debit_amount": Decimal("500.00"),
                "credit_amount": Decimal("0.00"),
            },
        )
        balances.append(b)
    return balances


# ── list_balances Tests ──────────────────────────────────────────


class TestListBalances:
    """Tests for OpeningBalanceService.list_balances()."""

    def test_list_empty(self, db_session: Session):
        """Empty database returns empty list and zero count."""
        balances, total = OpeningBalanceService.list_balances(db_session)

        assert balances == []
        assert total == 0

    def test_list_pagination(
        self, db_session: Session, three_balances: list[OpeningBalance]
    ):
        """Skip/limit pagination returns correct subset and full total."""
        balances, total = OpeningBalanceService.list_balances(
            db_session, skip=0, limit=2
        )

        assert len(balances) == 2
        assert total == 3

    def test_list_ordering(
        self, db_session: Session, three_balances: list[OpeningBalance]
    ):
        """Balances are ordered by balance_id ASC."""
        balances, total = OpeningBalanceService.list_balances(db_session)

        assert total == 3
        assert len(balances) == 3

        ids = [b.balance_id for b in balances]
        assert ids == sorted(ids)


# ── get_balance Tests ────────────────────────────────────────────


class TestGetBalance:
    """Tests for OpeningBalanceService.get_balance()."""

    def test_get_success(
        self, db_session: Session, balance: OpeningBalance
    ):
        """Existing balance is returned correctly."""
        result = OpeningBalanceService.get_balance(
            db_session, balance.balance_id
        )

        assert result.balance_id == balance.balance_id
        assert result.period_id == balance.period_id
        assert result.account_id == balance.account_id
        assert result.debit_amount == Decimal("1000.00")
        assert result.credit_amount == Decimal("0.00")

    def test_get_not_found(self, db_session: Session):
        """Non-existent balance raises ValueError."""
        with pytest.raises(ValueError, match="OpeningBalance 999 not found"):
            OpeningBalanceService.get_balance(db_session, 999)


# ── create_balance Tests ─────────────────────────────────────────


class TestCreateBalance:
    """Tests for OpeningBalanceService.create_balance()."""

    def test_create_success(
        self,
        db_session: Session,
        period: AccountingPeriod,
        account: Account,
    ):
        """Balance is created with required fields and flush assigns balance_id."""
        result = OpeningBalanceService.create_balance(
            db_session,
            {
                "period_id": period.period_id,
                "account_id": account.account_id,
                "debit_amount": Decimal("2500.00"),
                "credit_amount": Decimal("100.00"),
            },
        )

        assert result.balance_id is not None
        assert result.period_id == period.period_id
        assert result.account_id == account.account_id
        assert result.debit_amount == Decimal("2500.00")
        assert result.credit_amount == Decimal("100.00")

        # Verify in DB
        db_result = db_session.execute(
            select(OpeningBalance).where(
                OpeningBalance.balance_id == result.balance_id
            )
        ).scalar_one_or_none()
        assert db_result is not None

    def test_create_duplicate(
        self,
        db_session: Session,
        balance: OpeningBalance,
        period: AccountingPeriod,
        account: Account,
    ):
        """Duplicate (period_id, account_id) raises ValueError."""
        with pytest.raises(
            ValueError,
            match="Opening balance for this period and account already exists",
        ):
            OpeningBalanceService.create_balance(
                db_session,
                {
                    "period_id": period.period_id,
                    "account_id": account.account_id,
                },
            )

    def test_create_missing_period_id(
        self, db_session: Session, account: Account
    ):
        """Missing period_id raises ValueError."""
        with pytest.raises(ValueError, match="period_id is required"):
            OpeningBalanceService.create_balance(
                db_session,
                {"account_id": account.account_id},
            )

    def test_create_missing_account_id(
        self, db_session: Session, period: AccountingPeriod
    ):
        """Missing account_id raises ValueError."""
        with pytest.raises(ValueError, match="account_id is required"):
            OpeningBalanceService.create_balance(
                db_session,
                {"period_id": period.period_id},
            )


# ── update_balance Tests ─────────────────────────────────────────


class TestUpdateBalance:
    """Tests for OpeningBalanceService.update_balance()."""

    def test_update_success(
        self, db_session: Session, balance: OpeningBalance
    ):
        """Debit/credit amounts can be updated."""
        updated = OpeningBalanceService.update_balance(
            db_session,
            balance.balance_id,
            {
                "debit_amount": Decimal("5000.00"),
                "credit_amount": Decimal("200.00"),
            },
        )

        assert updated.debit_amount == Decimal("5000.00")
        assert updated.credit_amount == Decimal("200.00")
        assert updated.balance_id == balance.balance_id

    def test_update_duplicate(
        self,
        db_session: Session,
        period: AccountingPeriod,
        account: Account,
        second_account: Account,
    ):
        """Updating to existing (period, account) combo raises ValueError."""
        # Create two balances with different accounts
        b1 = OpeningBalanceService.create_balance(
            db_session,
            {
                "period_id": period.period_id,
                "account_id": account.account_id,
                "debit_amount": Decimal("100.00"),
            },
        )
        OpeningBalanceService.create_balance(
            db_session,
            {
                "period_id": period.period_id,
                "account_id": second_account.account_id,
                "debit_amount": Decimal("200.00"),
            },
        )

        # Try to update b1 to b2's account_id
        with pytest.raises(
            ValueError,
            match="Opening balance for this period and account already exists",
        ):
            OpeningBalanceService.update_balance(
                db_session,
                b1.balance_id,
                {"account_id": second_account.account_id},
            )

    def test_update_not_found(self, db_session: Session):
        """Non-existent balance raises ValueError."""
        with pytest.raises(ValueError, match="OpeningBalance 999 not found"):
            OpeningBalanceService.update_balance(
                db_session, 999, {"debit_amount": Decimal("100.00")}
            )


# ── delete_balance Tests ─────────────────────────────────────────


class TestDeleteBalance:
    """Tests for OpeningBalanceService.delete_balance()."""

    def test_delete_success(
        self, db_session: Session, balance: OpeningBalance
    ):
        """Balance is deleted and subsequent get raises ValueError."""
        bid = balance.balance_id
        OpeningBalanceService.delete_balance(db_session, bid)

        with pytest.raises(ValueError, match=f"OpeningBalance {bid} not found"):
            OpeningBalanceService.get_balance(db_session, bid)

    def test_delete_not_found(self, db_session: Session):
        """Non-existent balance raises ValueError."""
        with pytest.raises(ValueError, match="OpeningBalance 999 not found"):
            OpeningBalanceService.delete_balance(db_session, 999)
