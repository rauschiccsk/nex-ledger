"""
AccountingPeriod service for NEX Ledger.

Handles CRUD operations for accounting periods (účtovné obdobia)
with temporal validation (start < end, no overlap within chart).
"""

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.accounting_period import AccountingPeriod
from app.models.opening_balance import OpeningBalance


class AccountingPeriodService:
    """Service for AccountingPeriod CRUD operations."""

    # ── CRUD ─────────────────────────────────────────────────────────

    @staticmethod
    def list_periods(
        session: Session, skip: int = 0, limit: int = 100, filters: dict | None = None
    ) -> tuple[list[AccountingPeriod], int]:
        """
        List accounting periods with pagination, ordered by start_date DESC.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (periods list, total count)
        """
        total = session.execute(
            select(func.count(AccountingPeriod.period_id))
        ).scalar()

        periods = (
            session.execute(
                select(AccountingPeriod)
                .order_by(AccountingPeriod.start_date.desc())
                .offset(skip)
                .limit(limit)
            )
            .scalars()
            .all()
        )

        return list(periods), total

    @staticmethod
    def get_period(session: Session, period_id: int) -> AccountingPeriod:
        """
        Get accounting period by ID.

        Args:
            session: Database session
            period_id: Primary key of the period

        Returns:
            AccountingPeriod object

        Raises:
            ValueError: If period not found
        """
        period = session.execute(
            select(AccountingPeriod).where(
                AccountingPeriod.period_id == period_id
            )
        ).scalar_one_or_none()

        if not period:
            raise ValueError(f"Period with ID {period_id} not found")

        return period

    @staticmethod
    def create_period(
        session: Session, period_data: dict
    ) -> AccountingPeriod:
        """
        Create a new accounting period.

        Validates required fields, temporal consistency (start < end),
        and no date overlap with existing periods in the same chart.

        Args:
            session: Database session
            period_data: Dict with period fields
                (chart_id, year, period_number, start_date, end_date required)

        Returns:
            Created AccountingPeriod object

        Raises:
            ValueError: If validation fails or period overlaps
        """
        for field in ("chart_id", "year", "period_number", "start_date", "end_date"):
            if not period_data.get(field) and period_data.get(field) != 0:
                raise ValueError(f"Missing required field: {field}")

        start_date = period_data["start_date"]
        end_date = period_data["end_date"]

        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")

        # Overlap check within the same chart
        chart_id = period_data["chart_id"]
        overlapping = session.execute(
            select(AccountingPeriod).where(
                and_(
                    AccountingPeriod.chart_id == chart_id,
                    or_(
                        and_(
                            AccountingPeriod.start_date <= start_date,
                            AccountingPeriod.end_date >= start_date,
                        ),
                        and_(
                            AccountingPeriod.start_date <= end_date,
                            AccountingPeriod.end_date >= end_date,
                        ),
                    ),
                )
            )
        ).scalar_one_or_none()

        if overlapping:
            raise ValueError(
                f"Period overlaps with existing period: "
                f"year={overlapping.year}, period={overlapping.period_number}"
            )

        period = AccountingPeriod(**period_data)
        session.add(period)
        session.flush()

        return period

    @staticmethod
    def update_period(
        session: Session, period_id: int, period_data: dict
    ) -> AccountingPeriod:
        """
        Update an existing accounting period.

        If dates are changed, re-validates temporal consistency.

        Args:
            session: Database session
            period_id: Primary key of the period to update
            period_data: Dict with fields to update

        Returns:
            Updated AccountingPeriod object

        Raises:
            ValueError: If period not found or validation fails
        """
        period = AccountingPeriodService.get_period(session, period_id)

        # PK is immutable
        period_data.pop("period_id", None)

        # Determine effective dates for validation
        new_start = period_data.get("start_date", period.start_date)
        new_end = period_data.get("end_date", period.end_date)

        if "start_date" in period_data or "end_date" in period_data:
            if new_start >= new_end:
                raise ValueError("start_date must be before end_date")

            # Overlap check (exclude current period)
            chart_id = period_data.get("chart_id", period.chart_id)
            overlapping = session.execute(
                select(AccountingPeriod).where(
                    and_(
                        AccountingPeriod.chart_id == chart_id,
                        AccountingPeriod.period_id != period_id,
                        or_(
                            and_(
                                AccountingPeriod.start_date <= new_start,
                                AccountingPeriod.end_date >= new_start,
                            ),
                            and_(
                                AccountingPeriod.start_date <= new_end,
                                AccountingPeriod.end_date >= new_end,
                            ),
                        ),
                    )
                )
            ).scalar_one_or_none()

            if overlapping:
                raise ValueError(
                    f"Period overlaps with existing period: "
                    f"year={overlapping.year}, period={overlapping.period_number}"
                )

        for key, value in period_data.items():
            setattr(period, key, value)

        session.flush()
        return period

    @staticmethod
    def delete_period(session: Session, period_id: int) -> None:
        """
        Delete an accounting period.

        Validates that the period is not referenced by opening balances.

        Args:
            session: Database session
            period_id: Primary key of the period to delete

        Raises:
            ValueError: If period not found or referenced by opening balances
        """
        period = AccountingPeriodService.get_period(session, period_id)

        # FK guard: check opening_balance references
        count = session.execute(
            select(func.count(OpeningBalance.balance_id)).where(
                OpeningBalance.period_id == period_id
            )
        ).scalar()

        if count > 0:
            raise ValueError(
                "Cannot delete period: referenced by opening balances"
            )

        session.delete(period)
        session.flush()
