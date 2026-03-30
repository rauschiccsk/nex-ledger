"""Common schemas používané naprieč všetkými endpointmi."""

from pydantic import BaseModel, ConfigDict, Field


class PaginatedResponse[T](BaseModel):
    """Generic stránkovaná odpoveď pre list endpointy.

    Používa sa pre konzistentné pagination responses naprieč všetkými entitami.

    Example:
        ```python
        from app.schemas.account import AccountRead
        from app.schemas.common import PaginatedResponse

        @router.get("/accounts", response_model=PaginatedResponse[AccountRead])
        def list_accounts(skip: int = 0, limit: int = 100):
            accounts = get_accounts(skip, limit)
            total = get_total_count()
            return PaginatedResponse(
                items=accounts,
                total=total,
                skip=skip,
                limit=limit
            )
        ```
    """

    items: list[T] = Field(description="List entít na aktuálnej stránke")
    total: int = Field(description="Celkový počet záznamov v databáze")
    skip: int = Field(description="Počet preskočených záznamov (offset)")
    limit: int = Field(description="Maximálny počet záznamov na stránke")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 0,
                "skip": 0,
                "limit": 100,
            }
        }
    )
