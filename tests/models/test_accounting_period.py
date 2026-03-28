"""Tests for AccountingPeriod model."""

from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.accounting_period import AccountingPeriod
from app.models.chart_of_accounts import ChartOfAccounts


def test_create_period(db_session):
    """Test vytvorenia účtovného obdobia."""
    chart = ChartOfAccounts(code="SK2025", name="Slovenská účtovná osnova 2025")
    db_session.add(chart)
    db_session.flush()

    period = AccountingPeriod(
        chart_id=chart.chart_id,
        year=2026,
        period_number=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        is_closed=False,
    )
    db_session.add(period)
    db_session.commit()

    assert period.period_id is not None
    assert period.chart_id == chart.chart_id
    assert period.year == 2026
    assert period.period_number == 1
    assert period.start_date == date(2026, 1, 1)
    assert period.end_date == date(2026, 1, 31)
    assert period.is_closed is False


def test_unique_constraint(db_session):
    """Test UNIQUE constraint na (chart_id, year, period_number)."""
    chart = ChartOfAccounts(code="SK2025", name="Slovenská účtovná osnova 2025")
    db_session.add(chart)
    db_session.flush()

    period1 = AccountingPeriod(
        chart_id=chart.chart_id,
        year=2026,
        period_number=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )
    db_session.add(period1)
    db_session.commit()

    period2 = AccountingPeriod(
        chart_id=chart.chart_id,
        year=2026,
        period_number=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )
    db_session.add(period2)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()


def test_fk_constraint(db_session):
    """Test FK constraint — period musí mať existujúcu chart_id."""
    period = AccountingPeriod(
        chart_id=99999,
        year=2026,
        period_number=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )
    db_session.add(period)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()


def test_cascade_delete(db_session):
    """Test CASCADE delete — zmazanie chart zmaže aj periods."""
    chart = ChartOfAccounts(code="SK2025", name="Slovenská účtovná osnova 2025")
    db_session.add(chart)
    db_session.flush()

    period = AccountingPeriod(
        chart_id=chart.chart_id,
        year=2026,
        period_number=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )
    db_session.add(period)
    db_session.commit()

    period_id = period.period_id

    # CASCADE delete via raw SQL to avoid ORM relationship issues
    db_session.execute(
        text("DELETE FROM chart_of_accounts WHERE chart_id = :id"),
        {"id": chart.chart_id},
    )
    db_session.commit()

    deleted_period = db_session.get(AccountingPeriod, period_id)
    assert deleted_period is None


def test_default_is_closed(db_session):
    """Test default hodnoty is_closed=false."""
    chart = ChartOfAccounts(code="SK2025", name="Slovenská účtovná osnova 2025")
    db_session.add(chart)
    db_session.flush()

    period = AccountingPeriod(
        chart_id=chart.chart_id,
        year=2026,
        period_number=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        # is_closed NOT specified — should default to false
    )
    db_session.add(period)
    db_session.commit()

    assert period.is_closed is False


def test_repr(db_session):
    """Test __repr__ formátovanie."""
    chart = ChartOfAccounts(code="SK2025", name="Slovenská účtovná osnova 2025")
    db_session.add(chart)
    db_session.flush()

    period = AccountingPeriod(
        chart_id=chart.chart_id,
        year=2026,
        period_number=3,
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
    )
    db_session.add(period)
    db_session.commit()

    repr_str = repr(period)
    assert "AccountingPeriod" in repr_str
    assert str(period.period_id) in repr_str
    assert "2026" in repr_str
    assert "3" in repr_str
