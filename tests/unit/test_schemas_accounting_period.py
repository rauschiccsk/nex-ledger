"""Unit testy pre AccountingPeriod Pydantic schemas."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.accounting_period import (
    AccountingPeriodCreate,
    AccountingPeriodRead,
    AccountingPeriodUpdate,
)


def test_accounting_period_create_valid():
    """Test validného AccountingPeriodCreate objektu."""
    period = AccountingPeriodCreate(
        chart_id=1,
        year=2025,
        period_number=1,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        is_closed=False,
    )
    assert period.chart_id == 1
    assert period.year == 2025
    assert period.period_number == 1
    assert period.start_date == date(2025, 1, 1)
    assert period.end_date == date(2025, 1, 31)
    assert period.is_closed is False


def test_accounting_period_create_minimal():
    """Test minimálnych required polí (is_closed má default False)."""
    period = AccountingPeriodCreate(
        chart_id=1,
        year=2025,
        period_number=1,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    )
    assert period.is_closed is False  # default value


def test_accounting_period_create_invalid_year():
    """Test validácie year field (< 2000 nie je povolené)."""
    with pytest.raises(ValidationError) as exc_info:
        AccountingPeriodCreate(
            chart_id=1,
            year=1999,
            period_number=1,
            start_date=date(1999, 1, 1),
            end_date=date(1999, 1, 31),
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("year",) for e in errors)


def test_accounting_period_create_invalid_period_number():
    """Test validácie period_number field (1-13 rozsah)."""
    with pytest.raises(ValidationError) as exc_info:
        AccountingPeriodCreate(
            chart_id=1,
            year=2025,
            period_number=14,  # mimo rozsah
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("period_number",) for e in errors)


def test_accounting_period_create_closing_period():
    """Test vytvorenia closing period (period_number = 13)."""
    period = AccountingPeriodCreate(
        chart_id=1,
        year=2025,
        period_number=13,
        start_date=date(2025, 12, 31),
        end_date=date(2025, 12, 31),
        is_closed=True,
    )
    assert period.period_number == 13
    assert period.is_closed is True


def test_accounting_period_read_from_orm():
    """Test AccountingPeriodRead ORM mode (from_attributes)."""

    class MockORM:
        period_id = 1
        chart_id = 1
        year = 2025
        period_number = 1
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)
        is_closed = False

    period_read = AccountingPeriodRead.model_validate(MockORM())
    assert period_read.period_id == 1
    assert period_read.chart_id == 1
    assert period_read.year == 2025
    assert period_read.period_number == 1
    assert period_read.start_date == date(2025, 1, 1)
    assert period_read.end_date == date(2025, 1, 31)
    assert period_read.is_closed is False


def test_accounting_period_update_optional_fields():
    """Test AccountingPeriodUpdate všetky polia optional."""
    update = AccountingPeriodUpdate()
    assert update.chart_id is None
    assert update.year is None
    assert update.period_number is None
    assert update.start_date is None
    assert update.end_date is None
    assert update.is_closed is None


def test_accounting_period_update_partial():
    """Test partial update (len is_closed)."""
    update = AccountingPeriodUpdate(is_closed=True)
    assert update.is_closed is True
    assert update.chart_id is None
    assert update.year is None
