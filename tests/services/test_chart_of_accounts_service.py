"""
Tests for ChartOfAccountsService CRUD operations.

Covers: list_charts, get_chart, create_chart, update_chart, delete_chart.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.account_type import AccountType
from app.models.chart_of_accounts import ChartOfAccounts
from app.models.currency import Currency
from app.services.chart_of_accounts_service import ChartOfAccountsService

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture()
def chart_sk(db_session: Session) -> ChartOfAccounts:
    """Create Slovak chart of accounts."""
    coa = ChartOfAccounts(code="SK-2025", name="Slovak Chart 2025")
    db_session.add(coa)
    db_session.flush()
    return coa


@pytest.fixture()
def chart_cz(db_session: Session) -> ChartOfAccounts:
    """Create Czech chart of accounts."""
    coa = ChartOfAccounts(code="CZ-2025", name="Czech Chart 2025")
    db_session.add(coa)
    db_session.flush()
    return coa


@pytest.fixture()
def multiple_charts(db_session: Session) -> list[ChartOfAccounts]:
    """Create 5 charts for pagination testing."""
    items = [
        ("AT-2025", "Austrian Chart 2025"),
        ("CZ-2025", "Czech Chart 2025"),
        ("DE-2025", "German Chart 2025"),
        ("HU-2025", "Hungarian Chart 2025"),
        ("SK-2025", "Slovak Chart 2025"),
    ]
    charts = []
    for code, name in items:
        coa = ChartOfAccounts(code=code, name=name)
        db_session.add(coa)
        db_session.flush()
        charts.append(coa)
    return charts


@pytest.fixture()
def chart_with_account(
    db_session: Session, chart_sk: ChartOfAccounts
) -> Account:
    """Create account referencing chart_sk for FK guard testing."""
    # AccountType
    at = AccountType(code="ASSET", name="Assets")
    db_session.add(at)
    db_session.flush()

    # Currency
    cur = Currency(currency_code="EUR", name="Euro", symbol="€")
    db_session.add(cur)
    db_session.flush()

    # Account referencing chart_sk
    account = Account(
        chart_id=chart_sk.chart_id,
        account_number="100",
        name="Cash",
        account_type_id=at.account_type_id,
        currency_code=cur.currency_code,
        level=1,
    )
    db_session.add(account)
    db_session.flush()

    return account


# ── list_charts Tests ────────────────────────────────────────────


class TestListCharts:
    """Tests for ChartOfAccountsService.list_charts()."""

    def test_list_charts_empty(self, db_session: Session):
        """Empty database returns empty list and zero count."""
        charts, total = ChartOfAccountsService.list_charts(db_session)

        assert charts == []
        assert total == 0

    def test_list_charts_pagination(
        self, db_session: Session, multiple_charts: list[ChartOfAccounts]
    ):
        """Skip/limit pagination returns correct subset."""
        charts, total = ChartOfAccountsService.list_charts(
            db_session, skip=1, limit=2
        )

        assert len(charts) == 2
        assert total == 5

    def test_list_charts_ordering(
        self, db_session: Session, multiple_charts: list[ChartOfAccounts]
    ):
        """Charts are ordered by chart_id ASC."""
        charts, total = ChartOfAccountsService.list_charts(db_session)

        assert total == 5
        assert len(charts) == 5

        ids = [c.chart_id for c in charts]
        assert ids == sorted(ids)


# ── get_chart Tests ──────────────────────────────────────────────


class TestGetChart:
    """Tests for ChartOfAccountsService.get_chart()."""

    def test_get_chart_success(
        self, db_session: Session, chart_sk: ChartOfAccounts
    ):
        """Existing chart is returned correctly."""
        result = ChartOfAccountsService.get_chart(
            db_session, chart_sk.chart_id
        )

        assert result.chart_id == chart_sk.chart_id
        assert result.code == "SK-2025"
        assert result.name == "Slovak Chart 2025"

    def test_get_chart_not_found(self, db_session: Session):
        """Non-existent chart raises ValueError."""
        with pytest.raises(
            ValueError, match="ChartOfAccounts with ID 99999 not found"
        ):
            ChartOfAccountsService.get_chart(db_session, 99999)


# ── create_chart Tests ───────────────────────────────────────────


class TestCreateChart:
    """Tests for ChartOfAccountsService.create_chart()."""

    def test_create_chart_success(self, db_session: Session):
        """Chart is created with required fields."""
        chart = ChartOfAccountsService.create_chart(
            db_session,
            {"code": "SK-2025", "name": "Slovak Chart 2025"},
        )

        assert chart.code == "SK-2025"
        assert chart.name == "Slovak Chart 2025"
        assert chart.chart_id is not None

        # Verify in DB
        result = db_session.execute(
            select(ChartOfAccounts).where(
                ChartOfAccounts.chart_id == chart.chart_id
            )
        ).scalar_one_or_none()
        assert result is not None
        assert result.code == "SK-2025"

    def test_create_chart_missing_name(self, db_session: Session):
        """Missing name raises ValueError."""
        with pytest.raises(ValueError, match="Missing required field: name"):
            ChartOfAccountsService.create_chart(
                db_session,
                {"code": "SK-2025"},
            )

    def test_create_chart_missing_code(self, db_session: Session):
        """Missing code raises ValueError."""
        with pytest.raises(ValueError, match="Missing required field: code"):
            ChartOfAccountsService.create_chart(
                db_session,
                {"name": "Slovak Chart 2025"},
            )


# ── update_chart Tests ───────────────────────────────────────────


class TestUpdateChart:
    """Tests for ChartOfAccountsService.update_chart()."""

    def test_update_chart_success(
        self, db_session: Session, chart_sk: ChartOfAccounts
    ):
        """Chart fields can be updated."""
        updated = ChartOfAccountsService.update_chart(
            db_session,
            chart_sk.chart_id,
            {"name": "Slovak Chart 2025 (updated)", "description": "Updated desc"},
        )

        assert updated.name == "Slovak Chart 2025 (updated)"
        assert updated.description == "Updated desc"
        assert updated.code == "SK-2025"

    def test_update_chart_not_found(self, db_session: Session):
        """Non-existent chart raises ValueError."""
        with pytest.raises(
            ValueError, match="ChartOfAccounts with ID 99999 not found"
        ):
            ChartOfAccountsService.update_chart(
                db_session, 99999, {"name": "Ghost"}
            )


# ── delete_chart Tests ───────────────────────────────────────────


class TestDeleteChart:
    """Tests for ChartOfAccountsService.delete_chart()."""

    def test_delete_chart_success(
        self, db_session: Session, chart_sk: ChartOfAccounts
    ):
        """Unreferenced chart is deleted successfully."""
        chart_id = chart_sk.chart_id
        ChartOfAccountsService.delete_chart(db_session, chart_id)

        # Verify chart no longer exists
        result = db_session.execute(
            select(ChartOfAccounts).where(
                ChartOfAccounts.chart_id == chart_id
            )
        ).scalar_one_or_none()
        assert result is None

    def test_delete_chart_with_accounts(
        self, db_session: Session, chart_sk: ChartOfAccounts, chart_with_account: Account
    ):
        """Chart referenced by accounts cannot be deleted."""
        with pytest.raises(
            ValueError,
            match=r"Cannot delete ChartOfAccounts: 1 account\(s\) reference it",
        ):
            ChartOfAccountsService.delete_chart(
                db_session, chart_sk.chart_id
            )

    def test_delete_chart_not_found(self, db_session: Session):
        """Non-existent chart raises ValueError."""
        with pytest.raises(
            ValueError, match="ChartOfAccounts with ID 99999 not found"
        ):
            ChartOfAccountsService.delete_chart(db_session, 99999)
