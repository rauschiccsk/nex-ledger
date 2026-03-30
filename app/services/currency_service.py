"""
Currency service for NEX Ledger.

Handles CRUD operations for currencies with natural key (currency_code).
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.currency import Currency
from app.models.journal_entry_line import JournalEntryLine


class CurrencyService:
    """Service for currency CRUD operations."""

    # ── CRUD ─────────────────────────────────────────────────────────

    @staticmethod
    def list_currencies(
        session: Session, skip: int = 0, limit: int = 100
    ) -> tuple[list[Currency], int]:
        """
        List currencies with pagination, ordered by currency_code ASC.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (currencies list, total count)
        """
        total = session.execute(
            select(func.count(Currency.currency_code))
        ).scalar()

        currencies = (
            session.execute(
                select(Currency)
                .order_by(Currency.currency_code.asc())
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

        return list(currencies), total

    @staticmethod
    def get_currency(session: Session, currency_code: str) -> Currency:
        """
        Get currency by code.

        Args:
            session: Database session
            currency_code: ISO 4217 currency code (e.g., EUR, USD)

        Returns:
            Currency object

        Raises:
            ValueError: If currency not found
        """
        currency = session.execute(
            select(Currency).where(Currency.currency_code == currency_code)
        ).scalar_one_or_none()

        if not currency:
            raise ValueError(f"Currency not found: {currency_code}")

        return currency

    @staticmethod
    def create_currency(session: Session, currency_data: dict) -> Currency:
        """
        Create a new currency.

        Args:
            session: Database session
            currency_data: Dict with currency fields (currency_code, name required)

        Returns:
            Created Currency object

        Raises:
            ValueError: If validation fails or duplicate code exists
        """
        code = currency_data.get("currency_code")
        code = CurrencyService._validate_currency_code(code)
        currency_data["currency_code"] = code

        name = currency_data.get("name")
        if not name:
            raise ValueError("Currency name is required")

        # Duplicate check
        existing = session.execute(
            select(Currency).where(Currency.currency_code == code)
        ).scalar_one_or_none()

        if existing:
            raise ValueError(f"Currency already exists: {code}")

        currency = Currency(**currency_data)
        session.add(currency)
        session.flush()

        return currency

    @staticmethod
    def update_currency(
        session: Session, currency_code: str, currency_data: dict
    ) -> Currency:
        """
        Update an existing currency.

        Args:
            session: Database session
            currency_code: Currency code to update
            currency_data: Dict with fields to update

        Returns:
            Updated Currency object

        Raises:
            ValueError: If currency not found
        """
        currency = CurrencyService.get_currency(session, currency_code)

        # PK is immutable — remove currency_code from update data
        currency_data.pop("currency_code", None)

        for key, value in currency_data.items():
            setattr(currency, key, value)

        session.flush()
        return currency

    @staticmethod
    def delete_currency(session: Session, currency_code: str) -> None:
        """
        Delete a currency.

        Validates that the currency is not referenced by any journal entry lines.

        Args:
            session: Database session
            currency_code: Currency code to delete

        Raises:
            ValueError: If currency not found or in use by journal entry lines
        """
        currency = CurrencyService.get_currency(session, currency_code)

        # FK validation: check journal_entry_line references
        usage_count = session.execute(
            select(func.count(JournalEntryLine.line_id)).where(
                JournalEntryLine.currency_code == currency_code
            )
        ).scalar()

        if usage_count > 0:
            raise ValueError(
                f"Cannot delete currency {currency_code}: in use"
            )

        session.delete(currency)
        session.flush()

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _validate_currency_code(code: str | None) -> str:
        """
        Validate and normalize currency code.

        Args:
            code: Raw currency code input

        Returns:
            Uppercase 3-character currency code

        Raises:
            ValueError: If code is missing or not 3 characters
        """
        if not code or len(code) != 3:
            raise ValueError("Currency code must be 3 characters")
        return code.upper()
