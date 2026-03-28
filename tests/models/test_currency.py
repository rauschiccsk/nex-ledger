"""Tests for Currency model."""

import time
from datetime import datetime

from app.models.currency import Currency


def test_create_currency(db_session):
    """Test creating currency records with different decimal places."""
    # Create EUR
    eur = Currency(
        currency_code="EUR",
        name="Euro",
        symbol="€",
        decimal_places=2,
    )
    db_session.add(eur)

    # Create USD
    usd = Currency(
        currency_code="USD",
        name="US Dollar",
        symbol="$",
        decimal_places=2,
    )
    db_session.add(usd)

    db_session.commit()

    # Verify
    assert db_session.query(Currency).count() == 2

    eur_db = db_session.query(Currency).filter_by(currency_code="EUR").first()
    assert eur_db is not None
    assert eur_db.name == "Euro"
    assert eur_db.symbol == "€"
    assert eur_db.decimal_places == 2
    assert eur_db.is_active is True
    assert isinstance(eur_db.updated_at, datetime)


def test_currency_updated_at(db_session):
    """Test that updated_at changes on update."""
    # Create currency
    jpy = Currency(
        currency_code="JPY",
        name="Japanese Yen",
        symbol="¥",
        decimal_places=0,
    )
    db_session.add(jpy)
    db_session.commit()

    original_updated_at = jpy.updated_at

    # Wait 1 second to ensure timestamp difference
    time.sleep(1)

    # Update currency
    jpy.name = "Yen"
    db_session.commit()

    # Verify updated_at changed
    db_session.refresh(jpy)
    assert jpy.updated_at > original_updated_at


def test_currency_default_values(db_session):
    """Test server-side default values."""
    # Create currency without decimal_places and is_active
    gbp = Currency(
        currency_code="GBP",
        name="British Pound",
        symbol="£",
    )
    db_session.add(gbp)
    db_session.commit()

    # Refresh to get server defaults
    db_session.refresh(gbp)

    assert gbp.decimal_places == 2  # Server default
    assert gbp.is_active is True  # Server default
    assert gbp.updated_at is not None


def test_currency_deactivation(db_session):
    """Test deactivating currency (business rule: never delete, just deactivate)."""
    czk = Currency(
        currency_code="CZK",
        name="Czech Koruna",
        symbol="Kč",
        decimal_places=2,
    )
    db_session.add(czk)
    db_session.commit()

    # Deactivate
    czk.is_active = False
    db_session.commit()

    # Verify still exists in DB
    czk_db = db_session.query(Currency).filter_by(currency_code="CZK").first()
    assert czk_db is not None
    assert czk_db.is_active is False
