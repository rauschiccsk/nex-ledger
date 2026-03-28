"""
Journal Entry business logic service.

Handles double-entry validation and balance calculations.
"""
from decimal import Decimal
from typing import Tuple

from sqlalchemy.orm import Session

from app.models.journal_entry_line import JournalEntryLine


class JournalEntryService:
    """Service for journal entry operations."""

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
            ValueError: If sum of debits != sum of credits
        """
        lines = (
            session.query(JournalEntryLine)
            .filter_by(entry_id=entry_id)
            .all()
        )

        if not lines:
            raise ValueError(f"No lines found for entry {entry_id}")

        total_debit = sum(line.debit_amount for line in lines)
        total_credit = sum(line.credit_amount for line in lines)

        if total_debit != total_credit:
            raise ValueError(
                f"Entry {entry_id} is unbalanced: "
                f"debit={total_debit}, credit={total_credit}"
            )

        return True

    @staticmethod
    def get_entry_balance(
        session: Session, entry_id: int
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate total debit and credit for journal entry.

        Args:
            session: SQLAlchemy sync session
            entry_id: Journal entry ID (entry_id column)

        Returns:
            Tuple of (total_debit, total_credit)
        """
        lines = (
            session.query(JournalEntryLine)
            .filter_by(entry_id=entry_id)
            .all()
        )

        total_debit = sum(line.debit_amount for line in lines)
        total_credit = sum(line.credit_amount for line in lines)

        return (total_debit, total_credit)
