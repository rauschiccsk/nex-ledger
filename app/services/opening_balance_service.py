"""
Opening balance service for NEX Ledger.

Handles CRUD operations for opening balances (per account per accounting period).
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.opening_balance import OpeningBalance


class OpeningBalanceService:
    """Service for opening balance CRUD operations."""

    # ── CRUD ─────────────────────────────────────────────────────────

    @staticmethod
    def list_balances(
        session: Session, skip: int = 0, limit: int = 100, filters: dict | None = None
    ) -> tuple[list[OpeningBalance], int]:
        """
        List opening balances with pagination, ordered by balance_id ASC.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (balances list, total count)
        """
        total = session.execute(
            select(func.count(OpeningBalance.balance_id))
        ).scalar()

        balances = (
            session.execute(
                select(OpeningBalance)
                .order_by(OpeningBalance.balance_id.asc())
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

        return list(balances), total

    @staticmethod
    def get_balance(session: Session, balance_id: int) -> OpeningBalance:
        """
        Get opening balance by ID.

        Args:
            session: Database session
            balance_id: Opening balance primary key

        Returns:
            OpeningBalance object

        Raises:
            ValueError: If balance not found
        """
        balance = session.execute(
            select(OpeningBalance).where(
                OpeningBalance.balance_id == balance_id
            )
        ).scalar_one_or_none()

        if not balance:
            raise ValueError(f"OpeningBalance {balance_id} not found")

        return balance

    @staticmethod
    def create_balance(
        session: Session, balance_data: dict
    ) -> OpeningBalance:
        """
        Create a new opening balance.

        Args:
            session: Database session
            balance_data: Dict with balance fields (period_id, account_id required)

        Returns:
            Created OpeningBalance object

        Raises:
            ValueError: If required fields missing or duplicate (period_id, account_id)
        """
        period_id = balance_data.get("period_id")
        if period_id is None:
            raise ValueError("period_id is required")

        account_id = balance_data.get("account_id")
        if account_id is None:
            raise ValueError("account_id is required")

        # Unique constraint check: (period_id, account_id)
        existing_count = session.execute(
            select(func.count(OpeningBalance.balance_id)).where(
                OpeningBalance.period_id == period_id,
                OpeningBalance.account_id == account_id,
            )
        ).scalar()

        if existing_count > 0:
            raise ValueError(
                "Opening balance for this period and account already exists"
            )

        balance = OpeningBalance(**balance_data)
        session.add(balance)
        session.flush()

        return balance

    @staticmethod
    def update_balance(
        session: Session, balance_id: int, balance_data: dict
    ) -> OpeningBalance:
        """
        Update an existing opening balance.

        Args:
            session: Database session
            balance_id: Opening balance primary key
            balance_data: Dict with fields to update

        Returns:
            Updated OpeningBalance object

        Raises:
            ValueError: If balance not found or duplicate (period_id, account_id)
        """
        balance = OpeningBalanceService.get_balance(session, balance_id)

        updatable = ("debit_amount", "credit_amount")
        for key, value in balance_data.items():
            if key in updatable:
                setattr(balance, key, value)

        session.flush()
        return balance

    @staticmethod
    def delete_balance(session: Session, balance_id: int) -> None:
        """
        Delete an opening balance.

        Args:
            session: Database session
            balance_id: Opening balance primary key

        Raises:
            ValueError: If balance not found
        """
        balance = OpeningBalanceService.get_balance(session, balance_id)
        session.delete(balance)
        session.flush()
