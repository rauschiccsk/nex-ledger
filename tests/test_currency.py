"""Tests for Currency model — constraints, inserts, and validation."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import DatabaseError, IntegrityError

from app.models.currency import Currency


def test_currency_insert(db_session):
    """Test basic currency insert with valid data."""
    eur = Currency(code="EUR", name="Euro", symbol="€", decimal_places=2)
    db_session.add(eur)
    db_session.commit()

    result = db_session.execute(
        select(Currency).where(Currency.code == "EUR")
    ).scalar_one()
    assert result.code == "EUR"
    assert result.name == "Euro"
    assert result.symbol == "€"
    assert result.decimal_places == 2
    assert result.is_active is True
    assert result.id is not None
    assert result.created_at is not None


def test_currency_unique_code(db_session):
    """Test UNIQUE constraint on code."""
    usd1 = Currency(code="USD", name="US Dollar", symbol="$", decimal_places=2)
    db_session.add(usd1)
    db_session.commit()

    usd2 = Currency(code="USD", name="Another USD", symbol="$", decimal_places=2)
    db_session.add(usd2)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_currency_decimal_places_check_valid(db_session):
    """Test valid decimal_places values (0, 2, 4, 8)."""
    for places in [0, 2, 4, 8]:
        curr = Currency(
            code=f"T{places:02d}",
            name=f"Test {places}",
            symbol="T",
            decimal_places=places,
        )
        db_session.add(curr)
        db_session.commit()

    # Verify all 4 were inserted
    result = db_session.execute(select(Currency)).scalars().all()
    assert len(result) == 4


def test_currency_decimal_places_check_invalid_negative(db_session):
    """Test CHECK constraint rejects decimal_places = -1.

    Note: pg8000 maps CHECK violation (23514) to ProgrammingError,
    not IntegrityError. We catch DatabaseError (parent of both).
    """
    curr_neg = Currency(
        code="NEG", name="Negative", symbol="N", decimal_places=-1
    )
    db_session.add(curr_neg)
    with pytest.raises(DatabaseError, match="ck_currency_decimal_places"):
        db_session.commit()


def test_currency_decimal_places_check_invalid_over(db_session):
    """Test CHECK constraint rejects decimal_places = 9."""
    curr_over = Currency(
        code="OVR", name="Over", symbol="O", decimal_places=9
    )
    db_session.add(curr_over)
    with pytest.raises(DatabaseError, match="ck_currency_decimal_places"):
        db_session.commit()


def test_currency_insert_eur_usd_czk(db_session):
    """Test insert of EUR, USD, CZK currencies."""
    currencies = [
        Currency(code="EUR", name="Euro", symbol="€", decimal_places=2),
        Currency(code="USD", name="US Dollar", symbol="$", decimal_places=2),
        Currency(code="CZK", name="Czech Koruna", symbol="Kč", decimal_places=2),
    ]
    db_session.add_all(currencies)
    db_session.commit()

    result = (
        db_session.execute(select(Currency).order_by(Currency.code))
        .scalars()
        .all()
    )
    assert len(result) == 3
    assert [c.code for c in result] == ["CZK", "EUR", "USD"]


def test_currency_repr(db_session):
    """Test __repr__ method."""
    eur = Currency(code="EUR", name="Euro", symbol="€", decimal_places=2)
    assert repr(eur) == "<Currency(code='EUR', name='Euro')>"
