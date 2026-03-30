"""
ChartOfAccounts service for NEX Ledger.

Handles CRUD operations for charts of accounts (účtové osnovy).
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.chart_of_accounts import ChartOfAccounts


class ChartOfAccountsService:
    """Service for ChartOfAccounts CRUD operations."""

    # ── CRUD ─────────────────────────────────────────────────────────

    @staticmethod
    def list_charts(
        session: Session, skip: int = 0, limit: int = 100, filters: dict | None = None
    ) -> tuple[list[ChartOfAccounts], int]:
        """
        List charts of accounts with pagination, ordered by chart_id ASC.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (charts list, total count)
        """
        total = session.execute(
            select(func.count(ChartOfAccounts.chart_id))
        ).scalar()

        charts = (
            session.execute(
                select(ChartOfAccounts)
                .order_by(ChartOfAccounts.chart_id.asc())
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

        return list(charts), total

    @staticmethod
    def get_chart(session: Session, chart_id: int) -> ChartOfAccounts:
        """
        Get chart of accounts by ID.

        Args:
            session: Database session
            chart_id: Primary key of the chart

        Returns:
            ChartOfAccounts object

        Raises:
            ValueError: If chart not found
        """
        chart = session.execute(
            select(ChartOfAccounts).where(
                ChartOfAccounts.chart_id == chart_id
            )
        ).scalar_one_or_none()

        if not chart:
            raise ValueError(
                f"ChartOfAccounts with ID {chart_id} not found"
            )

        return chart

    @staticmethod
    def create_chart(
        session: Session, chart_data: dict
    ) -> ChartOfAccounts:
        """
        Create a new chart of accounts.

        Args:
            session: Database session
            chart_data: Dict with chart fields (name, code required)

        Returns:
            Created ChartOfAccounts object

        Raises:
            ValueError: If required fields are missing
        """
        for field in ("name", "code"):
            if not chart_data.get(field):
                raise ValueError(f"Missing required field: {field}")

        chart = ChartOfAccounts(**chart_data)
        session.add(chart)
        session.flush()

        return chart

    @staticmethod
    def update_chart(
        session: Session, chart_id: int, chart_data: dict
    ) -> ChartOfAccounts:
        """
        Update an existing chart of accounts.

        Args:
            session: Database session
            chart_id: Primary key of the chart to update
            chart_data: Dict with fields to update (name, code, description)

        Returns:
            Updated ChartOfAccounts object

        Raises:
            ValueError: If chart not found
        """
        chart = ChartOfAccountsService.get_chart(session, chart_id)

        # PK is immutable — remove chart_id from update data
        chart_data.pop("chart_id", None)

        for key, value in chart_data.items():
            setattr(chart, key, value)

        session.flush()
        return chart

    @staticmethod
    def delete_chart(session: Session, chart_id: int) -> None:
        """
        Delete a chart of accounts.

        Validates that the chart is not referenced by any accounts.

        Args:
            session: Database session
            chart_id: Primary key of the chart to delete

        Raises:
            ValueError: If chart not found or referenced by accounts
        """
        chart = ChartOfAccountsService.get_chart(session, chart_id)

        # FK guard: check account references
        count = session.execute(
            select(func.count(Account.account_id)).where(
                Account.chart_id == chart_id
            )
        ).scalar()

        if count > 0:
            raise ValueError(
                f"Cannot delete ChartOfAccounts: {count} account(s) reference it"
            )

        session.delete(chart)
        session.flush()
