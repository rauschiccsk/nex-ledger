"""AccountingPeriod model — účtovné obdobie pre konkrétnu účtovnú osnovu."""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    SmallInteger,
    UniqueConstraint,
)
from sqlalchemy.sql import text

from app.models.base import Base


class AccountingPeriod(Base):
    """Účtovné obdobie (mesiac/kvartál/rok) pre konkrétnu účtovnú osnovu.

    Každá účtovná osnova má svoje účtovné obdobia. Obdobie môže byť uzavreté
    (is_closed=true), čo znemožňuje ďalšie účtovné záznamy v tom období.

    Attributes:
        period_id: Primárny kľúč
        chart_id: FK na chart_of_accounts
        year: Rok obdobia (napr. 2026)
        period_number: Číslo obdobia (1-12 pre mesiace, 1-4 pre kvartály, atď.)
        start_date: Začiatok obdobia
        end_date: Koniec obdobia
        is_closed: Či je obdobie uzavreté pre ďalšie záznamy
    """

    __tablename__ = "accounting_period"

    period_id = Column(Integer, primary_key=True, autoincrement=True)
    chart_id = Column(
        Integer,
        ForeignKey("chart_of_accounts.chart_id", ondelete="CASCADE"),
        nullable=False,
    )
    year = Column(Integer, nullable=False)
    period_number = Column(SmallInteger, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_closed = Column(Boolean, nullable=False, server_default=text("false"))

    __table_args__ = (
        UniqueConstraint(
            "chart_id",
            "year",
            "period_number",
            name="uq_chart_year_period",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AccountingPeriod(period_id={self.period_id}, chart_id={self.chart_id}, "
            f"year={self.year}, period_number={self.period_number}, is_closed={self.is_closed})>"
        )
