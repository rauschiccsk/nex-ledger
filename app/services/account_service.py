"""
Account service for NEX Ledger.

Handles CRUD operations, balance recalculation, and account statement generation.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.journal_entry import JournalEntry
from app.models.journal_entry_line import JournalEntryLine


class AccountService:
    """Service for account CRUD and balance operations."""

    # ── CRUD ─────────────────────────────────────────────────────────

    @staticmethod
    def list_accounts(
        session: Session, skip: int = 0, limit: int = 100
    ) -> tuple[list[Account], int]:
        """
        List accounts with pagination, ordered by account_number ASC.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (accounts list, total count)
        """
        total = session.execute(
            select(func.count(Account.account_id))
        ).scalar()

        accounts = (
            session.execute(
                select(Account)
                .order_by(Account.account_number.asc())
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

        return list(accounts), total

    @staticmethod
    def get_account(session: Session, account_id: int) -> Account:
        """
        Get account by ID.

        Args:
            session: Database session
            account_id: Account ID

        Returns:
            Account object

        Raises:
            ValueError: If account not found
        """
        account = session.execute(
            select(Account).where(Account.account_id == account_id)
        ).scalar_one_or_none()

        if not account:
            raise ValueError(f"Account {account_id} not found")

        return account

    @staticmethod
    def create_account(session: Session, account_data: dict) -> Account:
        """
        Create a new account.

        Args:
            session: Database session
            account_data: Dict with account fields (code, name, account_type_id required)

        Returns:
            Created Account object

        Raises:
            ValueError: If parent_account_id references non-existent account
        """
        parent_id = account_data.get("parent_account_id")
        if parent_id is not None:
            AccountService.get_account(session, parent_id)

        account = Account(**account_data)
        session.add(account)
        session.flush()

        return account

    @staticmethod
    def update_account(
        session: Session, account_id: int, account_data: dict
    ) -> Account:
        """
        Update an existing account.

        Args:
            session: Database session
            account_id: Account ID to update
            account_data: Dict with fields to update

        Returns:
            Updated Account object

        Raises:
            ValueError: If account not found, parent not found, or circular reference
        """
        account = AccountService.get_account(session, account_id)

        # Check parent_id changes for circular references
        new_parent_id = account_data.get("parent_account_id")
        if new_parent_id is not None:
            if new_parent_id == account_id:
                raise ValueError(
                    f"Cannot set account {account_id} as its own parent"
                )

            # Verify new parent exists
            AccountService.get_account(session, new_parent_id)

            # Recursive check: ensure new parent is not a descendant of this account
            AccountService._check_circular_reference(
                session, account_id, new_parent_id
            )

        for key, value in account_data.items():
            setattr(account, key, value)

        session.flush()
        return account

    @staticmethod
    def delete_account(session: Session, account_id: int) -> None:
        """
        Delete an account.

        Validates that the account has no child accounts and zero balance.

        Args:
            session: Database session
            account_id: Account ID to delete

        Raises:
            ValueError: If account not found, has children, or non-zero balance
        """
        account = AccountService.get_account(session, account_id)

        # Check for child accounts
        child_count = session.execute(
            select(func.count(Account.account_id)).where(
                Account.parent_account_id == account_id
            )
        ).scalar()

        if child_count > 0:
            raise ValueError(
                f"Cannot delete account {account_id}: "
                f"has {child_count} child accounts"
            )

        # Check balance is zero
        balance = session.execute(
            select(
                func.coalesce(func.sum(JournalEntryLine.debit_amount), Decimal(0))
                - func.coalesce(
                    func.sum(JournalEntryLine.credit_amount), Decimal(0)
                )
            ).where(JournalEntryLine.account_id == account_id)
        ).scalar()

        if balance != 0:
            raise ValueError(
                f"Cannot delete account {account_id}: "
                f"balance is {balance}, must be 0"
            )

        session.delete(account)
        session.flush()

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _check_circular_reference(
        session: Session, account_id: int, new_parent_id: int
    ) -> None:
        """
        Verify that new_parent_id is not a descendant of account_id.

        Walks up the parent chain from new_parent_id. If it encounters
        account_id, we have a circular reference.

        Raises:
            ValueError: If circular reference detected
        """
        current_id = new_parent_id
        visited: set[int] = set()

        while current_id is not None:
            if current_id in visited:
                break  # Broken chain (shouldn't happen) — stop
            visited.add(current_id)

            parent = session.execute(
                select(Account.parent_account_id).where(
                    Account.account_id == current_id
                )
            ).scalar_one_or_none()

            if parent == account_id:
                raise ValueError(
                    f"Cannot set account {new_parent_id} as parent of "
                    f"{account_id}: would create circular reference"
                )

            current_id = parent

    # ── Balance Operations ───────────────────────────────────────────

    @staticmethod
    def recalculate_balance(session: Session, account_id: int) -> Account:
        """
        Recalculate account current_balance from opening_balance + sum(debit) - sum(credit).

        Args:
            session: Database session
            account_id: Account ID to recalculate

        Returns:
            Updated Account object

        Raises:
            ValueError: If account not found
        """
        account = session.query(Account).filter_by(account_id=account_id).first()
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Sum all journal entry lines for this account
        result = session.query(
            func.sum(JournalEntryLine.debit_amount).label("total_debit"),
            func.sum(JournalEntryLine.credit_amount).label("total_credit"),
        ).filter(JournalEntryLine.account_id == account_id).first()

        total_debit = result.total_debit or Decimal("0.00")
        total_credit = result.total_credit or Decimal("0.00")
        opening_balance = account.opening_balance or Decimal("0.00")

        # current_balance = opening + debit - credit
        account.current_balance = opening_balance + total_debit - total_credit
        session.flush()

        return account

    @staticmethod
    def get_account_statement(
        session: Session, account_id: int, from_date: date, to_date: date
    ) -> list[dict]:
        """
        Generate account statement with running balance.

        Args:
            session: Database session
            account_id: Account ID
            from_date: Start date
            to_date: End date

        Returns:
            List of transaction dictionaries with running balance

        Raises:
            ValueError: If account not found
        """
        account = session.query(Account).filter_by(account_id=account_id).first()
        if not account:
            raise ValueError(f"Account {account_id} not found")

        # Get all journal entry lines for this account in date range
        lines = (
            session.query(JournalEntryLine, JournalEntry)
            .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.entry_id)
            .filter(
                JournalEntryLine.account_id == account_id,
                JournalEntry.entry_date >= from_date,
                JournalEntry.entry_date <= to_date,
            )
            .order_by(JournalEntry.entry_date, JournalEntry.entry_id)
            .all()
        )

        # Calculate running balance
        running_balance = account.opening_balance or Decimal("0.00")
        statement = []

        for line, entry in lines:
            debit = line.debit_amount or Decimal("0.00")
            credit = line.credit_amount or Decimal("0.00")
            running_balance += debit - credit

            statement.append({
                "date": entry.entry_date,
                "entry_id": entry.entry_id,
                "description": entry.description,
                "debit": debit,
                "credit": credit,
                "balance": running_balance,
            })

        return statement
