"""Pydantic schemas pre API requests/responses."""

from app.schemas.account_type import (
    AccountTypeCreate,
    AccountTypeRead,
    AccountTypeUpdate,
)
from app.schemas.business_partner import (
    BusinessPartnerCreate,
    BusinessPartnerRead,
    BusinessPartnerUpdate,
)
from app.schemas.chart_of_accounts import (
    ChartOfAccountsCreate,
    ChartOfAccountsRead,
    ChartOfAccountsUpdate,
)
from app.schemas.common import PaginatedResponse
from app.schemas.currency import CurrencyCreate, CurrencyRead, CurrencyUpdate
from app.schemas.tax_rate import TaxRateCreate, TaxRateRead, TaxRateUpdate

__all__ = [
    # AccountType
    "AccountTypeCreate",
    "AccountTypeRead",
    "AccountTypeUpdate",
    # BusinessPartner
    "BusinessPartnerCreate",
    "BusinessPartnerRead",
    "BusinessPartnerUpdate",
    # ChartOfAccounts
    "ChartOfAccountsCreate",
    "ChartOfAccountsRead",
    "ChartOfAccountsUpdate",
    # Common
    "PaginatedResponse",
    # Currency
    "CurrencyCreate",
    "CurrencyRead",
    "CurrencyUpdate",
    # TaxRate
    "TaxRateCreate",
    "TaxRateRead",
    "TaxRateUpdate",
]
