"""
Journal Entry business logic service.

Handles double-entry validation, balance calculations, and full CRUD
for JournalEntry and JournalEntryLine.
"""
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry
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

    # ──────────────────────────────────────────────
    # JournalEntry CRUD
    # ──────────────────────────────────────────────

    @staticmethod
    def list_entries(
        session: Session, skip: int = 0, limit: int = 100, filters: dict | None = None
    ) -> tuple[list[JournalEntry], int]:
        """Return paginated journal entries ordered by date DESC, id DESC.

        Args:
            session: SQLAlchemy sync session
            skip: Number of records to skip (OFFSET)
            limit: Maximum number of records to return (LIMIT)

        Returns:
            Tuple of (list of entries, total count)
        """
        total = (
            session.query(func.count(JournalEntry.entry_id)).scalar() or 0
        )
        entries = (
            session.query(JournalEntry)
            .order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return entries, total

    @staticmethod
    def get_entry(session: Session, entry_id: int) -> JournalEntry:
        """Fetch a single journal entry by ID.

        Args:
            session: SQLAlchemy sync session
            entry_id: Journal entry PK

        Returns:
            JournalEntry instance

        Raises:
            ValueError: If the entry does not exist
        """
        entry = session.query(JournalEntry).filter(
            JournalEntry.entry_id == entry_id
        ).first()
        if entry is None:
            raise ValueError(f"Journal entry {entry_id} not found")
        return entry

    @staticmethod
    def create_entry(
        session: Session, entry_data: dict
    ) -> JournalEntry:
        """Create a new journal entry, optionally with lines.

        Accepted keys in *entry_data*:
            entry_number, entry_date, description, batch_id, created_by
            lines (optional list[dict]) — each dict forwarded to create_line

        Args:
            session: SQLAlchemy sync session
            entry_data: Dictionary of entry attributes

        Returns:
            Created JournalEntry instance

        Raises:
            ValueError: When double-entry validation fails
        """
        lines_data = entry_data.pop("lines", None)

        entry = JournalEntry(
            entry_number=entry_data.get("entry_number"),
            entry_date=entry_data.get("entry_date"),
            description=entry_data.get("description"),
            batch_id=entry_data.get("batch_id"),
            created_by=entry_data.get("created_by"),
        )
        session.add(entry)
        session.flush()

        if lines_data:
            for line_dict in lines_data:
                line = JournalEntryLine(
                    entry_id=entry.entry_id,
                    line_number=line_dict.get("line_number"),
                    account_id=line_dict.get("account_id"),
                    debit_amount=line_dict.get("debit_amount", Decimal("0.00")),
                    credit_amount=line_dict.get("credit_amount", Decimal("0.00")),
                    description=line_dict.get("description"),
                    currency_code=line_dict.get("currency_code"),
                    partner_id=line_dict.get("partner_id"),
                    tax_rate_id=line_dict.get("tax_rate_id"),
                )
                session.add(line)
            session.flush()
            JournalEntryService.validate_double_entry(session, entry.entry_id)

        return entry

    @staticmethod
    def update_entry(
        session: Session, entry_id: int, entry_data: dict
    ) -> JournalEntry:
        """Update an existing journal entry.

        Keys that may be updated:
            entry_date, description, reference_number
        The ``lines`` key is ignored — use line CRUD methods instead.

        Args:
            session: SQLAlchemy sync session
            entry_id: Journal entry PK
            entry_data: Dictionary of fields to update

        Returns:
            Updated JournalEntry instance

        Raises:
            ValueError: If entry not found or revalidation fails
        """
        entry = JournalEntryService.get_entry(session, entry_id)

        updatable = ("entry_date", "description", "reference_number")
        for key in updatable:
            if key in entry_data:
                setattr(entry, key, entry_data[key])

        session.flush()

        # Revalidate if entry already has lines
        line_count = (
            session.query(func.count(JournalEntryLine.line_id))
            .filter(JournalEntryLine.entry_id == entry_id)
            .scalar()
        )
        if line_count:
            JournalEntryService.validate_double_entry(session, entry_id)

        return entry

    @staticmethod
    def delete_entry(session: Session, entry_id: int) -> None:
        """Delete a journal entry and all its lines.

        Args:
            session: SQLAlchemy sync session
            entry_id: Journal entry PK

        Raises:
            ValueError: If entry not found
        """
        entry = JournalEntryService.get_entry(session, entry_id)
        session.query(JournalEntryLine).filter(
            JournalEntryLine.entry_id == entry_id
        ).delete()
        session.delete(entry)
        session.flush()

    # ──────────────────────────────────────────────
    # JournalEntryLine CRUD
    # ──────────────────────────────────────────────

    @staticmethod
    def list_lines(
        session: Session, entry_id: int
    ) -> list[JournalEntryLine]:
        """Return all lines for a journal entry ordered by line_id.

        Args:
            session: SQLAlchemy sync session
            entry_id: Parent journal entry PK

        Returns:
            List of JournalEntryLine instances

        Raises:
            ValueError: If the parent entry does not exist
        """
        JournalEntryService.get_entry(session, entry_id)
        return (
            session.query(JournalEntryLine)
            .filter(JournalEntryLine.entry_id == entry_id)
            .order_by(JournalEntryLine.line_id)
            .all()
        )

    @staticmethod
    def get_line(
        session: Session, entry_id: int, line_id: int
    ) -> JournalEntryLine:
        """Fetch a single journal entry line.

        Args:
            session: SQLAlchemy sync session
            entry_id: Parent journal entry PK
            line_id: Line PK

        Returns:
            JournalEntryLine instance

        Raises:
            ValueError: If line not found or does not belong to entry
        """
        line = (
            session.query(JournalEntryLine)
            .filter(
                JournalEntryLine.line_id == line_id,
                JournalEntryLine.entry_id == entry_id,
            )
            .first()
        )
        if line is None:
            raise ValueError(
                f"Journal entry line {line_id} not found "
                f"or does not belong to entry {entry_id}"
            )
        return line

    @staticmethod
    def create_line(
        session: Session, entry_id: int, line_data: dict
    ) -> JournalEntryLine:
        """Create a new line on a journal entry.

        Accepted keys in *line_data*:
            line_number, account_id, debit_amount, credit_amount,
            description, currency_code, partner_id, tax_rate_id

        Args:
            session: SQLAlchemy sync session
            entry_id: Parent journal entry PK
            line_data: Dictionary of line attributes

        Returns:
            Created JournalEntryLine instance

        Raises:
            ValueError: If parent entry not found or revalidation fails
        """
        JournalEntryService.get_entry(session, entry_id)

        line = JournalEntryLine(
            entry_id=entry_id,
            line_number=line_data.get("line_number"),
            account_id=line_data.get("account_id"),
            debit_amount=line_data.get("debit_amount", Decimal("0.00")),
            credit_amount=line_data.get("credit_amount", Decimal("0.00")),
            description=line_data.get("description"),
            currency_code=line_data.get("currency_code"),
            partner_id=line_data.get("partner_id"),
            tax_rate_id=line_data.get("tax_rate_id"),
        )
        session.add(line)
        session.flush()

        JournalEntryService.validate_double_entry(session, entry_id)
        return line

    @staticmethod
    def update_line(
        session: Session, entry_id: int, line_id: int, line_data: dict
    ) -> JournalEntryLine:
        """Update an existing journal entry line.

        Updatable keys:
            line_number, account_id, debit_amount, credit_amount,
            description, currency_code, partner_id, tax_rate_id

        Args:
            session: SQLAlchemy sync session
            entry_id: Parent journal entry PK
            line_id: Line PK
            line_data: Dictionary of fields to update

        Returns:
            Updated JournalEntryLine instance

        Raises:
            ValueError: If line not found or revalidation fails
        """
        line = JournalEntryService.get_line(session, entry_id, line_id)

        updatable = (
            "line_number", "account_id", "debit_amount", "credit_amount",
            "description", "currency_code", "partner_id", "tax_rate_id",
        )
        for key in updatable:
            if key in line_data:
                setattr(line, key, line_data[key])

        session.flush()
        JournalEntryService.validate_double_entry(session, entry_id)
        return line

    @staticmethod
    def delete_line(
        session: Session, entry_id: int, line_id: int
    ) -> None:
        """Delete a journal entry line.

        After deletion, revalidates balance if the entry still has lines.

        Args:
            session: SQLAlchemy sync session
            entry_id: Parent journal entry PK
            line_id: Line PK

        Raises:
            ValueError: If line not found or revalidation fails
        """
        line = JournalEntryService.get_line(session, entry_id, line_id)
        session.delete(line)
        session.flush()

        # Revalidate if remaining lines exist
        remaining = (
            session.query(func.count(JournalEntryLine.line_id))
            .filter(JournalEntryLine.entry_id == entry_id)
            .scalar()
        )
        if remaining:
            JournalEntryService.validate_double_entry(session, entry_id)
