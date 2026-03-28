"""Tests for ChartOfAccounts model."""

import pytest
from sqlalchemy.exc import IntegrityError, ProgrammingError

from app.models.chart_of_accounts import ChartOfAccounts


def test_create_chart(db_session):
    """Test creating a chart of accounts with all fields."""
    chart = ChartOfAccounts(
        code="SK-UCTO-2024",
        name="Slovenská účtová osnova 2024",
        description="Účtová osnova pre SK firmy podľa zákona o účtovníctve",
    )
    db_session.add(chart)
    db_session.commit()

    assert chart.chart_id is not None
    assert chart.code == "SK-UCTO-2024"
    assert chart.name == "Slovenská účtová osnova 2024"
    assert chart.description is not None


def test_unique_code_constraint(db_session):
    """Test UNIQUE constraint on code prevents duplicates."""
    chart1 = ChartOfAccounts(code="SK-UCTO-2024", name="Chart 1")
    db_session.add(chart1)
    db_session.commit()

    chart2 = ChartOfAccounts(code="SK-UCTO-2024", name="Chart 2")
    db_session.add(chart2)

    with pytest.raises((IntegrityError, ProgrammingError)):
        db_session.commit()

    db_session.rollback()


def test_nullable_description(db_session):
    """Test description is nullable (no NOT NULL constraint)."""
    chart = ChartOfAccounts(code="CZ-UCTO-2024", name="Czech Chart")
    db_session.add(chart)
    db_session.commit()

    assert chart.chart_id is not None
    assert chart.description is None


def test_multiple_charts(db_session):
    """Test creating multiple charts with different codes (multi-tenant scenario)."""
    charts = [
        ChartOfAccounts(code="SK-UCTO-2024", name="Slovak Chart"),
        ChartOfAccounts(code="CZ-UCTO-2024", name="Czech Chart"),
        ChartOfAccounts(code="HU-UCTO-2024", name="Hungarian Chart"),
    ]

    for chart in charts:
        db_session.add(chart)
    db_session.commit()

    result = db_session.query(ChartOfAccounts).all()
    assert len(result) == 3
    assert {c.code for c in result} == {"SK-UCTO-2024", "CZ-UCTO-2024", "HU-UCTO-2024"}


def test_chart_repr(db_session):
    """Test __repr__ method produces informative string."""
    chart = ChartOfAccounts(code="SK-UCTO-2024", name="Slovak Chart")
    db_session.add(chart)
    db_session.commit()

    repr_str = repr(chart)
    assert "ChartOfAccounts" in repr_str
    assert "chart_id=" in repr_str
    assert "code='SK-UCTO-2024'" in repr_str
    assert "name='Slovak Chart'" in repr_str
