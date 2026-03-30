"""
BusinessPartner service for NEX Ledger.

Handles CRUD operations for business partners (customers and suppliers).
FK guard on delete checks journal_entry_line.partner_id references.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.business_partner import BusinessPartner
from app.models.journal_entry_line import JournalEntryLine


class BusinessPartnerService:
    """Service for business partner CRUD operations."""

    # ── CRUD ─────────────────────────────────────────────────────────

    @staticmethod
    def list_partners(
        session: Session, skip: int = 0, limit: int = 100, filters: dict | None = None
    ) -> tuple[list[BusinessPartner], int]:
        """
        List partners with pagination, ordered by partner_id ASC.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (partners list, total count)
        """
        query = session.query(BusinessPartner).order_by(
            BusinessPartner.partner_id.asc()
        )
        total = query.count()
        partners = query.offset(skip).limit(limit).all()

        return partners, total

    @staticmethod
    def get_partner(session: Session, partner_id: int) -> BusinessPartner:
        """
        Get business partner by ID.

        Args:
            session: Database session
            partner_id: Business partner primary key

        Returns:
            BusinessPartner object

        Raises:
            ValueError: If partner not found
        """
        partner = (
            session.query(BusinessPartner)
            .filter_by(partner_id=partner_id)
            .first()
        )

        if partner is None:
            raise ValueError(
                f"BusinessPartner with ID {partner_id} not found"
            )

        return partner

    @staticmethod
    def create_partner(
        session: Session, partner_data: dict
    ) -> BusinessPartner:
        """
        Create a new business partner.

        Args:
            session: Database session
            partner_data: Dict with partner fields (name required)

        Returns:
            Created BusinessPartner object

        Raises:
            ValueError: If name is missing
        """
        name = partner_data.get("name")
        if not name:
            raise ValueError("BusinessPartner name is required")

        partner = BusinessPartner(**partner_data)
        session.add(partner)
        session.flush()

        return partner

    @staticmethod
    def update_partner(
        session: Session, partner_id: int, partner_data: dict
    ) -> BusinessPartner:
        """
        Update an existing business partner.

        Args:
            session: Database session
            partner_id: Partner ID to update
            partner_data: Dict with fields to update

        Returns:
            Updated BusinessPartner object

        Raises:
            ValueError: If partner not found
        """
        partner = BusinessPartnerService.get_partner(session, partner_id)

        for key, value in partner_data.items():
            setattr(partner, key, value)

        session.flush()
        return partner

    @staticmethod
    def delete_partner(session: Session, partner_id: int) -> None:
        """
        Delete a business partner.

        Validates that the partner is not referenced by any journal entry lines.

        Args:
            session: Database session
            partner_id: Partner ID to delete

        Raises:
            ValueError: If partner not found or referenced by journal entries
        """
        partner = BusinessPartnerService.get_partner(session, partner_id)

        # FK guard: check journal_entry_line references
        usage = session.execute(
            select(func.count(JournalEntryLine.line_id)).where(
                JournalEntryLine.partner_id == partner_id
            )
        ).scalar()

        if usage > 0:
            raise ValueError(
                f"Cannot delete BusinessPartner {partner_id}: "
                f"referenced by {usage} journal entries"
            )

        session.delete(partner)
        session.flush()
