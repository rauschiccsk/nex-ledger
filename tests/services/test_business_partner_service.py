"""
Tests for BusinessPartnerService CRUD operations.

Covers: list_partners, get_partner, create_partner, update_partner, delete_partner.
14 tests in 5 classes.
"""
import datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.account_type import AccountType
from app.models.business_partner import BusinessPartner
from app.models.chart_of_accounts import ChartOfAccounts
from app.models.currency import Currency
from app.models.import_batch import ImportBatch
from app.models.journal_entry import JournalEntry
from app.models.journal_entry_line import JournalEntryLine
from app.services.business_partner_service import BusinessPartnerService

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture()
def partner(db_session: Session) -> BusinessPartner:
    """Create a single business partner."""
    p = BusinessPartner(
        partner_type="CUSTOMER",
        code="CUST001",
        name="Test Customer",
    )
    db_session.add(p)
    db_session.flush()
    return p


@pytest.fixture()
def five_partners(db_session: Session) -> list[BusinessPartner]:
    """Create 5 business partners for pagination testing."""
    partners = []
    for i in range(1, 6):
        p = BusinessPartner(
            partner_type="CUSTOMER",
            code=f"CUST{i:03d}",
            name=f"Customer {i}",
        )
        db_session.add(p)
        db_session.flush()
        partners.append(p)
    return partners


@pytest.fixture()
def partner_with_journal_line(
    db_session: Session, partner: BusinessPartner
) -> JournalEntryLine:
    """Create full FK chain: partner referenced by a journal entry line."""
    # AccountType
    at = AccountType(code="ASSET-BP", name="Asset (BP test)")
    db_session.add(at)
    db_session.flush()

    # ChartOfAccounts
    coa = ChartOfAccounts(code="BP-TEST", name="Chart for BP tests")
    db_session.add(coa)
    db_session.flush()

    # Currency
    currency = Currency(currency_code="EUR", name="Euro", symbol="€")
    db_session.add(currency)
    db_session.flush()

    # Account
    account = Account(
        chart_id=coa.chart_id,
        account_number="3110",
        name="Receivables",
        account_type_id=at.account_type_id,
        currency_code="EUR",
        level=1,
    )
    db_session.add(account)
    db_session.flush()

    # ImportBatch
    batch = ImportBatch(
        filename="bp-test.csv",
        file_hash="b" * 64,
        status="imported",
    )
    db_session.add(batch)
    db_session.flush()

    # JournalEntry
    entry = JournalEntry(
        batch_id=batch.batch_id,
        entry_number="BP-JE-001",
        entry_date=datetime.date(2026, 1, 15),
        description="Entry referencing partner",
    )
    db_session.add(entry)
    db_session.flush()

    # JournalEntryLine with partner_id
    line = JournalEntryLine(
        entry_id=entry.entry_id,
        line_number=1,
        account_id=account.account_id,
        partner_id=partner.partner_id,
        debit_amount=Decimal("500.00"),
        credit_amount=Decimal("0.00"),
        currency_code="EUR",
    )
    db_session.add(line)
    db_session.flush()

    return line


# ── list_partners Tests ──────────────────────────────────────────


class TestListPartners:
    """Tests for BusinessPartnerService.list_partners()."""

    def test_list_empty(self, db_session: Session):
        """Empty database returns empty list and zero count."""
        partners, total = BusinessPartnerService.list_partners(db_session)

        assert partners == []
        assert total == 0

    def test_list_with_pagination(
        self, db_session: Session, five_partners: list[BusinessPartner]
    ):
        """Skip/limit pagination returns correct subset (3rd and 4th)."""
        partners, total = BusinessPartnerService.list_partners(
            db_session, skip=2, limit=2
        )

        assert len(partners) == 2
        assert total == 5
        # 3rd and 4th partners (ordered by partner_id ASC)
        assert partners[0].code == five_partners[2].code
        assert partners[1].code == five_partners[3].code

    def test_list_ordering(
        self, db_session: Session, five_partners: list[BusinessPartner]
    ):
        """Partners are ordered by partner_id ASC."""
        partners, total = BusinessPartnerService.list_partners(db_session)

        assert total == 5
        ids = [p.partner_id for p in partners]
        assert ids == sorted(ids)


# ── get_partner Tests ────────────────────────────────────────────


class TestGetPartner:
    """Tests for BusinessPartnerService.get_partner()."""

    def test_get_existing(
        self, db_session: Session, partner: BusinessPartner
    ):
        """Existing partner is returned correctly."""
        result = BusinessPartnerService.get_partner(
            db_session, partner.partner_id
        )

        assert result.partner_id == partner.partner_id
        assert result.name == "Test Customer"
        assert result.code == "CUST001"
        assert result.partner_type == "CUSTOMER"

    def test_get_nonexistent(self, db_session: Session):
        """Non-existent partner_id raises ValueError."""
        with pytest.raises(
            ValueError, match="BusinessPartner with ID 99999 not found"
        ):
            BusinessPartnerService.get_partner(db_session, 99999)


# ── create_partner Tests ─────────────────────────────────────────


class TestCreatePartner:
    """Tests for BusinessPartnerService.create_partner()."""

    def test_create_success(self, db_session: Session):
        """Partner is created with required fields and gets partner_id."""
        partner = BusinessPartnerService.create_partner(
            db_session,
            {
                "partner_type": "SUPPLIER",
                "code": "SUP001",
                "name": "Test Supplier",
            },
        )

        assert partner.partner_id is not None
        assert partner.name == "Test Supplier"
        assert partner.code == "SUP001"
        assert partner.partner_type == "SUPPLIER"

    def test_create_missing_name(self, db_session: Session):
        """Missing name raises ValueError."""
        with pytest.raises(
            ValueError, match="BusinessPartner name is required"
        ):
            BusinessPartnerService.create_partner(
                db_session,
                {"partner_type": "CUSTOMER", "code": "CUST999"},
            )

    def test_create_empty_name(self, db_session: Session):
        """Empty string name raises ValueError."""
        with pytest.raises(
            ValueError, match="BusinessPartner name is required"
        ):
            BusinessPartnerService.create_partner(
                db_session,
                {"partner_type": "CUSTOMER", "code": "CUST998", "name": ""},
            )

    def test_create_with_optional_fields(self, db_session: Session):
        """Partner with optional fields stores them correctly."""
        partner = BusinessPartnerService.create_partner(
            db_session,
            {
                "partner_type": "BOTH",
                "code": "BOTH001",
                "name": "Full Partner",
                "tax_id": "SK1234567890",
                "vat_number": "SK2099999999",
                "address": "Hlavná 1, 811 01 Bratislava",
                "contact_person": "Ján Novák",
                "email": "jan@example.com",
                "phone": "+421 900 000 000",
            },
        )

        assert partner.partner_id is not None
        assert partner.tax_id == "SK1234567890"
        assert partner.vat_number == "SK2099999999"
        assert partner.address == "Hlavná 1, 811 01 Bratislava"
        assert partner.contact_person == "Ján Novák"
        assert partner.email == "jan@example.com"
        assert partner.phone == "+421 900 000 000"


# ── update_partner Tests ─────────────────────────────────────────


class TestUpdatePartner:
    """Tests for BusinessPartnerService.update_partner()."""

    def test_update_success(
        self, db_session: Session, partner: BusinessPartner
    ):
        """Partner name is updated successfully."""
        updated = BusinessPartnerService.update_partner(
            db_session,
            partner.partner_id,
            {"name": "Updated Customer"},
        )

        assert updated.name == "Updated Customer"
        assert updated.partner_id == partner.partner_id

    def test_update_nonexistent(self, db_session: Session):
        """Non-existent partner_id raises ValueError."""
        with pytest.raises(
            ValueError, match="BusinessPartner with ID 99999 not found"
        ):
            BusinessPartnerService.update_partner(
                db_session, 99999, {"name": "Ghost"}
            )


# ── delete_partner Tests ─────────────────────────────────────────


class TestDeletePartner:
    """Tests for BusinessPartnerService.delete_partner()."""

    def test_delete_success(
        self, db_session: Session, partner: BusinessPartner
    ):
        """Unused partner is deleted successfully."""
        pid = partner.partner_id
        BusinessPartnerService.delete_partner(db_session, pid)

        # Verify partner no longer exists
        result = (
            db_session.query(BusinessPartner)
            .filter_by(partner_id=pid)
            .first()
        )
        assert result is None

    def test_delete_with_journal_entries(
        self,
        db_session: Session,
        partner: BusinessPartner,
        partner_with_journal_line: JournalEntryLine,
    ):
        """Partner referenced by journal entry line cannot be deleted."""
        with pytest.raises(
            ValueError,
            match=r"Cannot delete BusinessPartner \d+: referenced by 1 journal entries",
        ):
            BusinessPartnerService.delete_partner(
                db_session, partner.partner_id
            )

    def test_delete_nonexistent(self, db_session: Session):
        """Non-existent partner_id raises ValueError."""
        with pytest.raises(
            ValueError, match="BusinessPartner with ID 99999 not found"
        ):
            BusinessPartnerService.delete_partner(db_session, 99999)
