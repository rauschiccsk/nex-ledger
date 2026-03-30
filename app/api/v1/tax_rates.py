"""TaxRate CRUD endpoints.

Provides paginated list, read, create, update, and delete operations
for tax rates (VAT, sales tax, etc.).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tax_rate import TaxRate
from app.schemas.common import PaginatedResponse
from app.schemas.tax_rate import TaxRateCreate, TaxRateRead, TaxRateUpdate
from app.services.tax_rate_service import TaxRateService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[TaxRateRead],
    summary="List tax rates (paginated)",
)
def list_tax_rates(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=100, ge=1, le=1000, description="Max records per page"
    ),
    db: Session = Depends(get_db),
) -> PaginatedResponse[TaxRateRead]:
    """Return paginated list of tax rates ordered by tax_rate_id ASC."""
    items, total = TaxRateService.list_tax_rates(db, skip=skip, limit=limit)
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/{tax_rate_id}",
    response_model=TaxRateRead,
    summary="Get tax rate by ID",
)
def get_tax_rate(
    tax_rate_id: int,
    db: Session = Depends(get_db),
) -> TaxRateRead:
    """Return a single tax rate by primary key."""
    try:
        return TaxRateService.get_tax_rate(db, tax_rate_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TaxRate with ID {tax_rate_id} not found",
        )


@router.post(
    "",
    response_model=TaxRateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create tax rate",
)
def create_tax_rate(
    payload: TaxRateCreate,
    db: Session = Depends(get_db),
) -> TaxRateRead:
    """Create a new tax rate. Name must be unique."""
    # Check unique name
    existing = db.execute(
        select(TaxRate).where(TaxRate.name == payload.name)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"TaxRate with name '{payload.name}' already exists",
        )

    try:
        tax_rate = TaxRateService.create_tax_rate(db, payload.model_dump())
        db.commit()
        db.refresh(tax_rate)
        return tax_rate
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.put(
    "/{tax_rate_id}",
    response_model=TaxRateRead,
    summary="Update tax rate",
)
def update_tax_rate(
    tax_rate_id: int,
    payload: TaxRateUpdate,
    db: Session = Depends(get_db),
) -> TaxRateRead:
    """Update an existing tax rate. Name must remain unique."""
    # Check existence
    tax_rate = db.execute(
        select(TaxRate).where(TaxRate.tax_rate_id == tax_rate_id)
    ).scalar_one_or_none()

    if not tax_rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TaxRate with ID {tax_rate_id} not found",
        )

    # Validate unique name if being changed
    if payload.name is not None:
        existing = db.execute(
            select(TaxRate).where(
                TaxRate.name == payload.name,
                TaxRate.tax_rate_id != tax_rate_id,
            )
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"TaxRate with name '{payload.name}' already exists",
            )

    # Apply updates (only non-None fields)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tax_rate, key, value)

    db.flush()
    db.commit()
    db.refresh(tax_rate)
    return tax_rate


@router.delete(
    "/{tax_rate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tax rate",
)
def delete_tax_rate(
    tax_rate_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete a tax rate. Validates no journal entries reference this rate."""
    try:
        TaxRateService.delete_tax_rate(db, tax_rate_id)
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
