"""Unit testy pre ChartOfAccounts Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.chart_of_accounts import (
    ChartOfAccountsCreate,
    ChartOfAccountsRead,
    ChartOfAccountsUpdate,
)


def test_chart_of_accounts_create_valid():
    """Test vytvorenia ChartOfAccountsCreate s validnými dátami."""
    data = {
        "code": "SK01",
        "name": "Slovenský účtový rozvrh",
        "description": "Štandardný slovenský účtový rozvrh",
    }
    schema = ChartOfAccountsCreate(**data)
    assert schema.code == "SK01"
    assert schema.name == "Slovenský účtový rozvrh"
    assert schema.description == "Štandardný slovenský účtový rozvrh"


def test_chart_of_accounts_create_minimal():
    """Test vytvorenia ChartOfAccountsCreate s minimálnymi dátami."""
    data = {"code": "SK01", "name": "Slovenský účtový rozvrh"}
    schema = ChartOfAccountsCreate(**data)
    assert schema.code == "SK01"
    assert schema.name == "Slovenský účtový rozvrh"
    assert schema.description is None


def test_chart_of_accounts_create_code_too_long():
    """Test validácie max_length pre code."""
    data = {"code": "X" * 21, "name": "Test"}  # 21 znakov, max je 20
    with pytest.raises(ValidationError) as exc_info:
        ChartOfAccountsCreate(**data)
    assert "code" in str(exc_info.value)


def test_chart_of_accounts_create_name_too_long():
    """Test validácie max_length pre name."""
    data = {"code": "SK01", "name": "X" * 101}  # 101 znakov, max je 100
    with pytest.raises(ValidationError) as exc_info:
        ChartOfAccountsCreate(**data)
    assert "name" in str(exc_info.value)


def test_chart_of_accounts_read_orm_mode():
    """Test ChartOfAccountsRead s ORM objektom."""

    class MockORMObject:
        chart_id = 1
        code = "SK01"
        name = "Slovenský účtový rozvrh"
        description = "Popis"

    schema = ChartOfAccountsRead.model_validate(MockORMObject())
    assert schema.chart_id == 1
    assert schema.code == "SK01"
    assert schema.name == "Slovenský účtový rozvrh"
    assert schema.description == "Popis"


def test_chart_of_accounts_update_all_optional():
    """Test ChartOfAccountsUpdate — všetky polia optional."""
    schema = ChartOfAccountsUpdate()
    assert schema.code is None
    assert schema.name is None
    assert schema.description is None


def test_chart_of_accounts_update_partial():
    """Test ChartOfAccountsUpdate — partial update s jedným poľom."""
    data = {"name": "Nový názov"}
    schema = ChartOfAccountsUpdate(**data)
    assert schema.code is None
    assert schema.name == "Nový názov"
    assert schema.description is None
