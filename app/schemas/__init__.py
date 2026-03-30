"""Pydantic schemas pre API requests/responses."""

from app.schemas.account import AccountCreate, AccountRead, AccountUpdate
from app.schemas.account_type import (
    AccountTypeCreate,
    AccountTypeRead,
    AccountTypeUpdate,
)
from app.schemas.accounting_period import (
    AccountingPeriodCreate,
    AccountingPeriodRead,
    AccountingPeriodUpdate,
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
from app.schemas.import_batch import (
    ImportBatchCreate,
    ImportBatchRead,
    ImportBatchUpdate,
)
from app.schemas.tax_rate import TaxRateCreate, TaxRateRead, TaxRateUpdate

__all__ = [
    # Common
    "PaginatedResponse",
    # Currency
    "CurrencyCreate",
    "CurrencyRead",
    "CurrencyUpdate",
    # AccountType
    "AccountTypeCreate",
    "AccountTypeRead",
    "AccountTypeUpdate",
    # TaxRate
    "TaxRateCreate",
    "TaxRateRead",
    "TaxRateUpdate",
    # BusinessPartner
    "BusinessPartnerCreate",
    "BusinessPartnerRead",
    "BusinessPartnerUpdate",
    # ChartOfAccounts
    "ChartOfAccountsCreate",
    "ChartOfAccountsRead",
    "ChartOfAccountsUpdate",
    # ImportBatch
    "ImportBatchCreate",
    "ImportBatchRead",
    "ImportBatchUpdate",
    # AccountingPeriod
    "AccountingPeriodCreate",
    "AccountingPeriodRead",
    "AccountingPeriodUpdate",
    # Account
    "AccountCreate",
    "AccountRead",
    "AccountUpdate",
]
