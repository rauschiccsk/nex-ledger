"""
AccountType service for NEX Ledger.

Handles CRUD operations for account types (ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE).
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.account_type import AccountType

_VALID_NORMAL_BALANCES = {"debit", "credit"}


class AccountTypeService:
    """Service for account type CRUD operations."""

    # ── CRUD ─────────────────────────────────────────────────────────

    @staticmethod
    def list_account_types(
        session: Session, skip: int = 0, limit: int = 100
    ) -> tuple[list[AccountType], int]:
        """
        List account types with pagination, ordered by account_type_id ASC.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (account_types list, total count)
        """
        total = session.execute(
            select(func.count(AccountType.account_type_id))
        ).scalar()

        account_types = (
            session.execute(
                select(AccountType)
                .order_by(AccountType.account_type_id.asc())
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

        return list(account_types), total

    @staticmethod
    def get_account_type(session: Session, account_type_id: int) -> AccountType:
        """
        Get account type by ID.

        Args:
            session: Database session
            account_type_id: Account type primary key

        Returns:
            AccountType object

        Raises:
            ValueError: If account type not found
        """
        account_type = session.execute(
            select(AccountType).where(
                AccountType.account_type_id == account_type_id
            )
        ).scalar_one_or_none()

        if not account_type:
            raise ValueError(
                f"AccountType s ID {account_type_id} neexistuje"
            )

        return account_type

    @staticmethod
    def create_account_type(
        session: Session, account_type_data: dict
    ) -> AccountType:
        """
        Create a new account type.

        Args:
            session: Database session
            account_type_data: Dict with account type fields
                (name, normal_balance required)

        Returns:
            Created AccountType object

        Raises:
            ValueError: If validation fails (missing name/normal_balance,
                invalid normal_balance value)
        """
        name = account_type_data.get("name")
        if not name:
            raise ValueError("Account type name is required")

        normal_balance = account_type_data.get("normal_balance")
        if not normal_balance:
            raise ValueError("Account type normal_balance is required")

        if normal_balance not in _VALID_NORMAL_BALANCES:
            raise ValueError(
                f"normal_balance must be 'debit' or 'credit', got: {normal_balance!r}"
            )

        # Remove normal_balance from data — not a DB column
        db_data = {
            k: v for k, v in account_type_data.items() if k != "normal_balance"
        }

        account_type = AccountType(**db_data)
        session.add(account_type)
        session.flush()

        return account_type

    @staticmethod
    def update_account_type(
        session: Session, account_type_id: int, account_type_data: dict
    ) -> AccountType:
        """
        Update an existing account type.

        Args:
            session: Database session
            account_type_id: Account type ID to update
            account_type_data: Dict with fields to update

        Returns:
            Updated AccountType object

        Raises:
            ValueError: If account type not found
        """
        account_type = AccountTypeService.get_account_type(
            session, account_type_id
        )

        # Remove normal_balance from update data — not a DB column
        update_data = {
            k: v for k, v in account_type_data.items() if k != "normal_balance"
        }

        for key, value in update_data.items():
            setattr(account_type, key, value)

        session.flush()
        return account_type

    @staticmethod
    def delete_account_type(
        session: Session, account_type_id: int
    ) -> None:
        """
        Delete an account type.

        Validates that the account type is not referenced by any accounts.

        Args:
            session: Database session
            account_type_id: Account type ID to delete

        Raises:
            ValueError: If account type not found or in use by accounts
        """
        account_type = AccountTypeService.get_account_type(
            session, account_type_id
        )

        # FK validation: check account references
        usage_count = session.execute(
            select(func.count(Account.account_id)).where(
                Account.account_type_id == account_type_id
            )
        ).scalar()

        if usage_count > 0:
            raise ValueError(
                f"AccountType {account_type_id} je použitý v {usage_count} "
                f"účtoch a nemôže byť zmazaný"
            )

        session.delete(account_type)
        session.flush()
