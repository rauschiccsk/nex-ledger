"""
TaxRate service for NEX Ledger.

Handles CRUD operations for tax rates (VAT, sales tax, etc.).
"""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.journal_entry_line import JournalEntryLine
from app.models.tax_rate import TaxRate


class TaxRateService:
    """Service for tax rate CRUD operations."""

    # ── CRUD ─────────────────────────────────────────────────────────

    @staticmethod
    def list_tax_rates(
        session: Session, skip: int = 0, limit: int = 100, filters: dict | None = None
    ) -> tuple[list[TaxRate], int]:
        """
        List tax rates with pagination, ordered by tax_rate_id ASC.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (tax_rates list, total count)
        """
        total = session.execute(
            select(func.count(TaxRate.tax_rate_id))
        ).scalar()

        tax_rates = (
            session.execute(
                select(TaxRate)
                .order_by(TaxRate.tax_rate_id.asc())
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

        return list(tax_rates), total

    @staticmethod
    def get_tax_rate(session: Session, tax_rate_id: int) -> TaxRate:
        """
        Get tax rate by ID.

        Args:
            session: Database session
            tax_rate_id: Tax rate primary key

        Returns:
            TaxRate object

        Raises:
            ValueError: If tax rate not found
        """
        tax_rate = session.execute(
            select(TaxRate).where(TaxRate.tax_rate_id == tax_rate_id)
        ).scalar_one_or_none()

        if not tax_rate:
            raise ValueError(f"TaxRate {tax_rate_id} not found")

        return tax_rate

    @staticmethod
    def create_tax_rate(
        session: Session, tax_rate_data: dict
    ) -> TaxRate:
        """
        Create a new tax rate.

        Args:
            session: Database session
            tax_rate_data: Dict with tax rate fields
                (name, rate required)

        Returns:
            Created TaxRate object

        Raises:
            ValueError: If validation fails (missing name or rate)
        """
        name = tax_rate_data.get("name")
        if not name:
            raise ValueError("Tax rate name is required")

        rate = tax_rate_data.get("rate")
        if rate is None:
            raise ValueError("Tax rate rate is required")

        # Ensure rate is Decimal for Numeric column
        if not isinstance(rate, Decimal):
            tax_rate_data = {**tax_rate_data, "rate": Decimal(str(rate))}

        tax_rate = TaxRate(**tax_rate_data)
        session.add(tax_rate)
        session.flush()

        return tax_rate

    @staticmethod
    def update_tax_rate(
        session: Session, tax_rate_id: int, tax_rate_data: dict
    ) -> TaxRate:
        """
        Update an existing tax rate.

        Args:
            session: Database session
            tax_rate_id: Tax rate ID to update
            tax_rate_data: Dict with fields to update

        Returns:
            Updated TaxRate object

        Raises:
            ValueError: If tax rate not found
        """
        tax_rate = TaxRateService.get_tax_rate(session, tax_rate_id)

        for key, value in tax_rate_data.items():
            setattr(tax_rate, key, value)

        session.flush()
        return tax_rate

    @staticmethod
    def delete_tax_rate(
        session: Session, tax_rate_id: int
    ) -> None:
        """
        Delete a tax rate.

        Validates that the tax rate is not referenced by any journal entry lines.

        Args:
            session: Database session
            tax_rate_id: Tax rate ID to delete

        Raises:
            ValueError: If tax rate not found or in use by journal entry lines
        """
        tax_rate = TaxRateService.get_tax_rate(session, tax_rate_id)

        # FK validation: check journal entry line references
        usage_count = session.execute(
            select(func.count(JournalEntryLine.line_id)).where(
                JournalEntryLine.tax_rate_id == tax_rate_id
            )
        ).scalar()

        if usage_count > 0:
            raise ValueError(
                "Cannot delete tax_rate with journal entries"
            )

        session.delete(tax_rate)
        session.flush()
