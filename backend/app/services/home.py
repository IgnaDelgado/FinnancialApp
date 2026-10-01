from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.cash_flow import cash_flow_snapshot
from app.domain.currency import Currency
from app.domain.planning import financial_today, month_bounds
from app.repositories.home import HomeRepository
from app.schemas.home import CashFlowResponse, HomeResponse
from app.services.planning import PlanningService


class HomeService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def snapshot(self, user_id: UUID) -> HomeResponse:
        today = financial_today()
        start, end = month_bounds(today.year, today.month)
        planning = PlanningService(self._session)
        planning.ensure_monthly_records(user_id, "income", start, end)
        planning.ensure_monthly_records(user_id, "commitments", start, end)
        account_values, bill_values, income_values = HomeRepository(
            self._session
        ).inputs(user_id, end)
        currencies = []
        for currency in Currency:
            result = cash_flow_snapshot(
                currency, today, end, account_values, bill_values, income_values
            )
            currencies.append(
                CashFlowResponse(
                    currency=currency,
                    liquid_cash=result.liquid_cash,
                    pending_bills=result.pending_bills,
                    expected_income=result.expected_income,
                    negative_balances=result.negative_balances,
                    overdue_income_count=result.overdue_income_count,
                    cash_after_bills=result.cash_after_bills,
                    forecast_after_bills=result.forecast_after_bills,
                )
            )
        return HomeResponse(
            today=today,
            month_end=end,
            account_count=len(account_values),
            commitment_count=len(bill_values),
            currencies=currencies,
        )
