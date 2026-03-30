"""BusinessPartner CRUD endpoints.

Provides paginated list, read, create, update, and delete operations
for business partners (customers, suppliers, or both).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.business_partner import BusinessPartner
from app.schemas.business_partner import (
    BusinessPartnerCreate,
    BusinessPartnerRead,
    BusinessPartnerUpdate,
)
from app.schemas.common import PaginatedResponse
from app.services.business_partner_service import BusinessPartnerService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[BusinessPartnerRead],
    summary="List business partners (paginated)",
)
def list_business_partners(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=100, ge=1, le=1000, description="Max records per page"
    ),
    db: Session = Depends(get_db),
) -> PaginatedResponse[BusinessPartnerRead]:
    """Return paginated list of business partners ordered by partner_id ASC."""
    items, total = BusinessPartnerService.list_partners(db, skip=skip, limit=limit)
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/{partner_id}",
    response_model=BusinessPartnerRead,
    summary="Get business partner by ID",
)
def get_business_partner(
    partner_id: int,
    db: Session = Depends(get_db),
) -> BusinessPartnerRead:
    """Return a single business partner by primary key."""
    try:
        return BusinessPartnerService.get_partner(db, partner_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BusinessPartner with ID {partner_id} not found",
        )


@router.post(
    "",
    response_model=BusinessPartnerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create business partner",
)
def create_business_partner(
    payload: BusinessPartnerCreate,
    db: Session = Depends(get_db),
) -> BusinessPartnerRead:
    """Create a new business partner. Code and tax_id must be unique."""
    # Check unique code (registration_number)
    if payload.code is not None:
        existing = db.execute(
            select(BusinessPartner).where(BusinessPartner.code == payload.code)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"BusinessPartner with code '{payload.code}' already exists",
            )

    # Check unique tax_id (tax_number) if provided
    if payload.tax_id is not None:
        existing = db.execute(
            select(BusinessPartner).where(BusinessPartner.tax_id == payload.tax_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"BusinessPartner with tax_id '{payload.tax_id}' already exists",
            )

    try:
        partner = BusinessPartnerService.create_partner(db, payload.model_dump())
        db.commit()
        db.refresh(partner)
        return partner
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.put(
    "/{partner_id}",
    response_model=BusinessPartnerRead,
    summary="Update business partner",
)
def update_business_partner(
    partner_id: int,
    payload: BusinessPartnerUpdate,
    db: Session = Depends(get_db),
) -> BusinessPartnerRead:
    """Update an existing business partner. Code and tax_id must remain unique."""
    # Check existence
    partner = db.execute(
        select(BusinessPartner).where(
            BusinessPartner.partner_id == partner_id
        )
    ).scalar_one_or_none()

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BusinessPartner with ID {partner_id} not found",
        )

    # Validate unique code if being changed
    if payload.code is not None:
        existing = db.execute(
            select(BusinessPartner).where(
                BusinessPartner.code == payload.code,
                BusinessPartner.partner_id != partner_id,
            )
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"BusinessPartner with code '{payload.code}' already exists",
            )

    # Validate unique tax_id if being changed
    if payload.tax_id is not None:
        existing = db.execute(
            select(BusinessPartner).where(
                BusinessPartner.tax_id == payload.tax_id,
                BusinessPartner.partner_id != partner_id,
            )
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"BusinessPartner with tax_id '{payload.tax_id}' already exists",
            )

    # Apply updates (only non-None fields)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(partner, key, value)

    db.flush()
    db.commit()
    db.refresh(partner)
    return partner


@router.delete(
    "/{partner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete business partner",
)
def delete_business_partner(
    partner_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete a business partner. Validates no journal entries reference this partner."""
    try:
        BusinessPartnerService.delete_partner(db, partner_id)
        db.commit()
    except ValueError as e:
        db.rollback()
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_msg,
        )
