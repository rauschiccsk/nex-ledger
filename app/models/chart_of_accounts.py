"""ChartOfAccounts model — účtová osnova (accounting framework).

Business rules:
- code: unikátny identifikátor osnovy (napr. 'SK-UCTO-2024')
- name: názov osnovy (napr. 'Slovenská účtová osnova 2024')
- description: voliteľný popis
"""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.schema import UniqueConstraint

from app.models.base import Base


class ChartOfAccounts(Base):
    """Chart of Accounts (účtová osnova) - defines accounting framework."""

    __tablename__ = "chart_of_accounts"

    chart_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    __table_args__ = (UniqueConstraint("code", name="uq_chart_of_accounts_code"),)

    def __repr__(self) -> str:
        return (
            f"<ChartOfAccounts(chart_id={self.chart_id}, code='{self.code}', name='{self.name}')>"
        )
