"""
Account balance reconciliation service for NEX Ledger.

Handles balance recalculation and account statement generation.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.journal_entry import JournalEntry
from app.models.journal_entry_line import JournalEntryLine


class AccountService:
    """Service for account balance operations."""

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
