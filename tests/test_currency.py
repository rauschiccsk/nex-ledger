"""Tests for Currency model constraints."""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.orm import sessionmaker

from app.database import settings
from app.models import Currency
from app.models.base import Base


@pytest.fixture(scope="function")
def db_session():
    """Create test database session with fresh schema."""
    engine = create_engine(settings.database_url)

    # Ensure uuid-ossp extension exists
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        conn.commit()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


def test_insert_currencies(db_session):
    """Test inserting EUR, USD, CZK currencies."""
    currencies = [
        Currency(code="EUR", name="Euro", symbol="\u20ac", decimal_places=2),
        Currency(code="USD", name="US Dollar", symbol="$", decimal_places=2),
        Currency(code="CZK", name="Czech Koruna", symbol="K\u010d", decimal_places=2),
    ]

    db_session.add_all(currencies)
    db_session.commit()

    # Verify all inserted
    assert db_session.query(Currency).count() == 3

    # Verify EUR details
    eur = db_session.query(Currency).filter_by(code="EUR").first()
    assert eur.name == "Euro"
    assert eur.symbol == "\u20ac"
    assert eur.decimal_places == 2
    assert eur.is_active is True
    assert eur.id is not None  # UUID generated
    assert eur.created_at is not None
    assert eur.updated_at is not None


def test_unique_code_constraint(db_session):
    """Test UNIQUE constraint on currency code."""
    # Insert first EUR
    eur1 = Currency(code="EUR", name="Euro", symbol="\u20ac", decimal_places=2)
    db_session.add(eur1)
    db_session.commit()

    # Try to insert duplicate EUR code
    eur2 = Currency(code="EUR", name="European Euro", symbol="\u20ac", decimal_places=2)
    db_session.add(eur2)

    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    error_msg = str(exc_info.value).lower()
    assert "unique" in error_msg or "duplicate key" in error_msg
    db_session.rollback()


def test_decimal_places_check_constraint_reject_negative(db_session):
    """Test CHECK constraint rejects negative decimal_places."""
    btc = Currency(code="BTC", name="Bitcoin", symbol="\u20bf", decimal_places=-1)
    db_session.add(btc)

    # pg8000 maps CHECK violations (23514) to ProgrammingError, not IntegrityError
    with pytest.raises((IntegrityError, ProgrammingError)) as exc_info:
        db_session.commit()

    error_msg = str(exc_info.value).lower()
    assert "check" in error_msg or "ck_currency_decimal_places" in error_msg
    db_session.rollback()


def test_decimal_places_check_constraint_reject_too_large(db_session):
    """Test CHECK constraint rejects decimal_places > 8."""
    crypto = Currency(code="XYZ", name="Crypto", symbol="X", decimal_places=9)
    db_session.add(crypto)

    # pg8000 maps CHECK violations (23514) to ProgrammingError, not IntegrityError
    with pytest.raises((IntegrityError, ProgrammingError)) as exc_info:
        db_session.commit()

    error_msg = str(exc_info.value).lower()
    assert "check" in error_msg or "ck_currency_decimal_places" in error_msg
    db_session.rollback()


def test_decimal_places_check_constraint_accept_valid(db_session):
    """Test CHECK constraint accepts valid decimal_places (0-8)."""
    # Edge case: 0 decimals (e.g., JPY)
    jpy = Currency(code="JPY", name="Japanese Yen", symbol="\u00a5", decimal_places=0)
    db_session.add(jpy)
    db_session.commit()

    # Edge case: 8 decimals (max)
    btc = Currency(code="BTC", name="Bitcoin", symbol="\u20bf", decimal_places=8)
    db_session.add(btc)
    db_session.commit()

    assert db_session.query(Currency).filter_by(code="JPY").first().decimal_places == 0
    assert db_session.query(Currency).filter_by(code="BTC").first().decimal_places == 8
