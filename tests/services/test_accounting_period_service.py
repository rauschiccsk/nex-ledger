"""
Tests for AccountingPeriodService CRUD operations.

Covers: list_periods, get_period, create_period, update_period, delete_period.
"""

import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.account_type import AccountType
from app.models.accounting_period import AccountingPeriod
from app.models.chart_of_accounts import ChartOfAccounts
from app.models.currency import Currency
from app.models.opening_balance import OpeningBalance
from app.services.accounting_period_service import AccountingPeriodService

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture()
def sample_chart(db_session: Session) -> ChartOfAccounts:
    """Create a chart of accounts for period tests."""
    coa = ChartOfAccounts(code="SK-2024", name="Slovak Chart 2024")
    db_session.add(coa)
    db_session.flush()
    return coa


@pytest.fixture()
def sample_period(
    db_session: Session, sample_chart: ChartOfAccounts
) -> AccountingPeriod:
    """Create accounting period 2024-01-01 to 2024-12-31."""
    period = AccountingPeriod(
        chart_id=sample_chart.chart_id,
        year=2024,
        period_number=1,
        start_date=datetime.date(2024, 1, 1),
        end_date=datetime.date(2024, 12, 31),
    )
    db_session.add(period)
    db_session.flush()
    return period


# ── list_periods Tests ───────────────────────────────────────────


class TestListPeriods:
    """Tests for AccountingPeriodService.list_periods()."""

    def test_list_periods_empty(self, db_session: Session):
        """Empty database returns empty list and zero count."""
        periods, total = AccountingPeriodService.list_periods(db_session)

        assert periods == []
        assert total == 0

    def test_list_periods_pagination(
        self,
        db_session: Session,
        sample_chart: ChartOfAccounts,
    ):
        """Skip/limit pagination returns correct subset."""
        # Create 3 periods
        for i in range(3):
            p = AccountingPeriod(
                chart_id=sample_chart.chart_id,
                year=2024,
                period_number=i + 1,
                start_date=datetime.date(2024, 1 + i * 4, 1),
                end_date=datetime.date(2024, (i + 1) * 4, 28),
            )
            db_session.add(p)
        db_session.flush()

        periods, total = AccountingPeriodService.list_periods(
            db_session, skip=1, limit=1
        )

        assert len(periods) == 1
        assert total == 3

    def test_list_periods_ordering(
        self,
        db_session: Session,
        sample_chart: ChartOfAccounts,
    ):
        """Periods are ordered by start_date DESC (newest first)."""
        p1 = AccountingPeriod(
            chart_id=sample_chart.chart_id,
            year=2024,
            period_number=1,
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2024, 3, 31),
        )
        p2 = AccountingPeriod(
            chart_id=sample_chart.chart_id,
            year=2024,
            period_number=2,
            start_date=datetime.date(2024, 4, 1),
            end_date=datetime.date(2024, 6, 30),
        )
        p3 = AccountingPeriod(
            chart_id=sample_chart.chart_id,
            year=2024,
            period_number=3,
            start_date=datetime.date(2024, 7, 1),
            end_date=datetime.date(2024, 9, 30),
        )
        db_session.add_all([p1, p2, p3])
        db_session.flush()

        periods, total = AccountingPeriodService.list_periods(db_session)

        assert total == 3
        dates = [p.start_date for p in periods]
        assert dates == sorted(dates, reverse=True)


# ── get_period Tests ─────────────────────────────────────────────


class TestGetPeriod:
    """Tests for AccountingPeriodService.get_period()."""

    def test_get_period_success(
        self, db_session: Session, sample_period: AccountingPeriod
    ):
        """Existing period is returned correctly."""
        result = AccountingPeriodService.get_period(
            db_session, sample_period.period_id
        )

        assert result.period_id == sample_period.period_id
        assert result.year == 2024
        assert result.period_number == 1
        assert result.start_date == datetime.date(2024, 1, 1)
        assert result.end_date == datetime.date(2024, 12, 31)

    def test_get_period_not_found(self, db_session: Session):
        """Non-existent period raises ValueError."""
        with pytest.raises(
            ValueError, match="Period with ID 99999 not found"
        ):
            AccountingPeriodService.get_period(db_session, 99999)


# ── create_period Tests ──────────────────────────────────────────


class TestCreatePeriod:
    """Tests for AccountingPeriodService.create_period()."""

    def test_create_period_success(
        self, db_session: Session, sample_chart: ChartOfAccounts
    ):
        """Period is created with all required fields."""
        period = AccountingPeriodService.create_period(
            db_session,
            {
                "chart_id": sample_chart.chart_id,
                "year": 2025,
                "period_number": 1,
                "start_date": datetime.date(2025, 1, 1),
                "end_date": datetime.date(2025, 12, 31),
            },
        )

        assert period.period_id is not None
        assert period.chart_id == sample_chart.chart_id
        assert period.year == 2025
        assert period.period_number == 1
        assert period.is_closed is False

        # Verify in DB
        result = db_session.execute(
            select(AccountingPeriod).where(
                AccountingPeriod.period_id == period.period_id
            )
        ).scalar_one_or_none()
        assert result is not None

    def test_create_period_missing_name(
        self, db_session: Session, sample_chart: ChartOfAccounts
    ):
        """Missing required field raises ValueError."""
        with pytest.raises(
            ValueError, match="Missing required field: start_date"
        ):
            AccountingPeriodService.create_period(
                db_session,
                {
                    "chart_id": sample_chart.chart_id,
                    "year": 2025,
                    "period_number": 1,
                    "end_date": datetime.date(2025, 12, 31),
                },
            )

    def test_create_period_invalid_dates(
        self, db_session: Session, sample_chart: ChartOfAccounts
    ):
        """start_date > end_date raises ValueError."""
        with pytest.raises(
            ValueError, match="start_date must be before end_date"
        ):
            AccountingPeriodService.create_period(
                db_session,
                {
                    "chart_id": sample_chart.chart_id,
                    "year": 2025,
                    "period_number": 1,
                    "start_date": datetime.date(2025, 12, 31),
                    "end_date": datetime.date(2025, 1, 1),
                },
            )

    def test_create_period_overlapping(
        self,
        db_session: Session,
        sample_chart: ChartOfAccounts,
        sample_period: AccountingPeriod,
    ):
        """Overlapping period raises ValueError."""
        with pytest.raises(ValueError, match="Period overlaps with existing"):
            AccountingPeriodService.create_period(
                db_session,
                {
                    "chart_id": sample_chart.chart_id,
                    "year": 2024,
                    "period_number": 2,
                    "start_date": datetime.date(2024, 6, 1),
                    "end_date": datetime.date(2025, 6, 30),
                },
            )


# ── update_period Tests ──────────────────────────────────────────


class TestUpdatePeriod:
    """Tests for AccountingPeriodService.update_period()."""

    def test_update_period_success(
        self, db_session: Session, sample_period: AccountingPeriod
    ):
        """Period fields can be updated (rename year)."""
        updated = AccountingPeriodService.update_period(
            db_session,
            sample_period.period_id,
            {"year": 2023},
        )

        assert updated.year == 2023
        assert updated.period_number == 1

    def test_update_period_not_found(self, db_session: Session):
        """Non-existent period raises ValueError."""
        with pytest.raises(
            ValueError, match="Period with ID 99999 not found"
        ):
            AccountingPeriodService.update_period(
                db_session, 99999, {"year": 2023}
            )

    def test_update_period_close_period(
        self, db_session: Session, sample_period: AccountingPeriod
    ):
        """Period can be closed with is_closed=True."""
        updated = AccountingPeriodService.update_period(
            db_session,
            sample_period.period_id,
            {"is_closed": True},
        )

        assert updated.is_closed is True


# ── delete_period Tests ──────────────────────────────────────────


class TestDeletePeriod:
    """Tests for AccountingPeriodService.delete_period()."""

    def test_delete_period_success(
        self, db_session: Session, sample_period: AccountingPeriod
    ):
        """Unreferenced period is deleted successfully."""
        period_id = sample_period.period_id
        AccountingPeriodService.delete_period(db_session, period_id)

        # Verify period no longer exists
        result = db_session.execute(
            select(AccountingPeriod).where(
                AccountingPeriod.period_id == period_id
            )
        ).scalar_one_or_none()
        assert result is None

    def test_delete_period_not_found(self, db_session: Session):
        """Non-existent period raises ValueError."""
        with pytest.raises(
            ValueError, match="Period with ID 99999 not found"
        ):
            AccountingPeriodService.delete_period(db_session, 99999)

    def test_delete_period_has_opening_balances(
        self,
        db_session: Session,
        sample_chart: ChartOfAccounts,
        sample_period: AccountingPeriod,
    ):
        """Period referenced by opening balances cannot be deleted."""
        # Create required dependencies for an account
        at = AccountType(code="ASSET", name="Assets")
        db_session.add(at)
        db_session.flush()

        cur = Currency(currency_code="EUR", name="Euro", symbol="€")
        db_session.add(cur)
        db_session.flush()

        account = Account(
            chart_id=sample_chart.chart_id,
            account_number="100",
            name="Cash",
            account_type_id=at.account_type_id,
            currency_code=cur.currency_code,
            level=1,
        )
        db_session.add(account)
        db_session.flush()

        # Create opening balance referencing the period
        ob = OpeningBalance(
            period_id=sample_period.period_id,
            account_id=account.account_id,
        )
        db_session.add(ob)
        db_session.flush()

        with pytest.raises(
            ValueError,
            match="Cannot delete period: referenced by opening balances",
        ):
            AccountingPeriodService.delete_period(
                db_session, sample_period.period_id
            )
