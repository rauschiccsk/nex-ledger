"""
Journal Entry business logic service.

Handles double-entry validation and balance calculations.
"""
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.journal_entry_line import JournalEntryLine


class JournalEntryService:
    """Service for journal entry operations."""

    @staticmethod
    def _sum_entry_amounts(
        session: Session, entry_id: int
    ) -> tuple[Decimal, Decimal]:
        """SQL-level aggregation of debit/credit for an entry.

        Returns (total_debit, total_credit) as Decimal.
        Returns (Decimal("0.00"), Decimal("0.00")) when no lines exist.
        """
        result = session.query(
            func.coalesce(func.sum(JournalEntryLine.debit_amount), Decimal("0.00")),
            func.coalesce(func.sum(JournalEntryLine.credit_amount), Decimal("0.00")),
        ).filter(
            JournalEntryLine.entry_id == entry_id
        ).one()

        return result[0], result[1]

    @staticmethod
    def validate_double_entry(session: Session, entry_id: int) -> bool:
        """
        Validate that journal entry follows double-entry bookkeeping rules.

        Args:
            session: SQLAlchemy sync session
            entry_id: Journal entry ID (entry_id column)

        Returns:
            True if balanced

        Raises:
            ValueError: If sum of debits != sum of credits or no lines exist
        """
        # Check that at least one line exists
        line_count = (
            session.query(func.count(JournalEntryLine.line_id))
            .filter(JournalEntryLine.entry_id == entry_id)
            .scalar()
        )

        if not line_count:
            raise ValueError(f"No lines found for entry {entry_id}")

        total_debit, total_credit = JournalEntryService._sum_entry_amounts(
            session, entry_id
        )

        if total_debit != total_credit:
            raise ValueError(
                f"Entry {entry_id} is unbalanced: "
                f"debit={total_debit}, credit={total_credit}"
            )

        return True

    @staticmethod
    def get_entry_balance(
        session: Session, entry_id: int
    ) -> tuple[Decimal, Decimal]:
        """
        Calculate total debit and credit for journal entry.

        Args:
            session: SQLAlchemy sync session
            entry_id: Journal entry ID (entry_id column)

        Returns:
            Tuple of (total_debit, total_credit) as Decimal
        """
        return JournalEntryService._sum_entry_amounts(session, entry_id)
