"""Unit testy pre AccountType Pydantic schemas."""

import pytest

from app.schemas.account_type import (
    AccountTypeCreate,
    AccountTypeRead,
    AccountTypeUpdate,
)


def test_account_type_create_valid():
    """Test validného AccountTypeCreate."""
    schema = AccountTypeCreate(
        code="ASSET",
        name="Assets",
        description="Asset accounts",
    )
    assert schema.code == "ASSET"
    assert schema.name == "Assets"
    assert schema.description == "Asset accounts"


def test_account_type_create_minimal():
    """Test AccountTypeCreate s minimálnymi poľami (description optional)."""
    schema = AccountTypeCreate(code="LIABILITY", name="Liabilities")
    assert schema.code == "LIABILITY"
    assert schema.name == "Liabilities"
    assert schema.description is None


def test_account_type_create_code_max_length():
    """Test validácie max_length pre code (20 znakov)."""
    with pytest.raises(ValueError, match="String should have at most 20 characters"):
        AccountTypeCreate(
            code="A" * 21,  # 21 znakov — prekročenie limitu
            name="Test",
        )


def test_account_type_create_name_max_length():
    """Test validácie max_length pre name (100 znakov)."""
    with pytest.raises(ValueError, match="String should have at most 100 characters"):
        AccountTypeCreate(
            code="TEST",
            name="N" * 101,  # 101 znakov — prekročenie limitu
        )


def test_account_type_read_from_orm():
    """Test AccountTypeRead s ORM objektom (from_attributes=True)."""

    # Simuluj ORM objekt
    class FakeORMAccountType:
        account_type_id = 1
        code = "EQUITY"
        name = "Equity"
        description = "Equity accounts"

    schema = AccountTypeRead.model_validate(FakeORMAccountType())
    assert schema.account_type_id == 1
    assert schema.code == "EQUITY"
    assert schema.name == "Equity"
    assert schema.description == "Equity accounts"


def test_account_type_update_optional_fields():
    """Test AccountTypeUpdate — všetky polia optional."""
    # Prázdny update (validný)
    schema = AccountTypeUpdate()
    assert schema.code is None
    assert schema.name is None
    assert schema.description is None

    # Partial update (len name)
    schema = AccountTypeUpdate(name="Updated Name")
    assert schema.code is None
    assert schema.name == "Updated Name"
    assert schema.description is None


def test_account_type_update_validation():
    """Test validácie v AccountTypeUpdate (max_length stále platí)."""
    with pytest.raises(ValueError, match="String should have at most 20 characters"):
        AccountTypeUpdate(code="A" * 21)

    with pytest.raises(ValueError, match="String should have at most 100 characters"):
        AccountTypeUpdate(name="N" * 101)
