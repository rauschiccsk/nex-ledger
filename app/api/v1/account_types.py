"""AccountType CRUD endpoints.

Provides paginated list, read, create, update, and delete operations
for account types (ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.account_type import AccountType
from app.schemas.account_type import AccountTypeCreate, AccountTypeRead, AccountTypeUpdate
from app.schemas.common import PaginatedResponse
from app.services.account_type_service import AccountTypeService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[AccountTypeRead],
    summary="List account types (paginated)",
)
def list_account_types(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max records per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AccountTypeRead]:
    """Return paginated list of account types ordered by account_type_id ASC."""
    items, total = AccountTypeService.list_account_types(db, skip=skip, limit=limit)
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/{account_type_id}",
    response_model=AccountTypeRead,
    summary="Get account type by ID",
)
def get_account_type(
    account_type_id: int,
    db: Session = Depends(get_db),
) -> AccountTypeRead:
    """Return a single account type by primary key."""
    try:
        return AccountTypeService.get_account_type(db, account_type_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AccountType with ID {account_type_id} not found",
        )


@router.post(
    "",
    response_model=AccountTypeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create account type",
)
def create_account_type(
    payload: AccountTypeCreate,
    db: Session = Depends(get_db),
) -> AccountTypeRead:
    """Create a new account type. Code must be unique, name must not be empty."""
    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Account type name must not be empty",
        )

    # Check unique code
    from sqlalchemy import select

    existing = db.execute(
        select(AccountType).where(AccountType.code == payload.code)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"AccountType with code '{payload.code}' already exists",
        )

    try:
        account_type = AccountTypeService.create_account_type(
            db, payload.model_dump()
        )
        db.commit()
        db.refresh(account_type)
        return account_type
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.put(
    "/{account_type_id}",
    response_model=AccountTypeRead,
    summary="Update account type",
)
def update_account_type(
    account_type_id: int,
    payload: AccountTypeUpdate,
    db: Session = Depends(get_db),
) -> AccountTypeRead:
    """Update an existing account type. Code must remain unique."""
    # Check existence
    from sqlalchemy import select

    account_type = db.execute(
        select(AccountType).where(
            AccountType.account_type_id == account_type_id
        )
    ).scalar_one_or_none()

    if not account_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AccountType with ID {account_type_id} not found",
        )

    # Validate unique code if being changed
    if payload.code is not None:
        existing = db.execute(
            select(AccountType).where(
                AccountType.code == payload.code,
                AccountType.account_type_id != account_type_id,
            )
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"AccountType with code '{payload.code}' already exists",
            )

    # Validate name not empty if provided
    if payload.name is not None and not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Account type name must not be empty",
        )

    # Apply updates (only non-None fields)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(account_type, key, value)

    db.flush()
    db.commit()
    db.refresh(account_type)
    return account_type


@router.delete(
    "/{account_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete account type",
)
def delete_account_type(
    account_type_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete an account type. Validates no accounts reference this type."""
    try:
        AccountTypeService.delete_account_type(db, account_type_id)
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
