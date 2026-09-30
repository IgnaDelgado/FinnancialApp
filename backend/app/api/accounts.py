from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_database_session
from app.models.user import User
from app.schemas.accounts import (
    AccountBalanceSnapshotResponse,
    AccountBalanceUpdateRequest,
    AccountCreateRequest,
    AccountResponse,
)
from app.services.financial_accounts import (
    AccountNotFoundError,
    FinancialAccountService,
)

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    request: AccountCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> AccountResponse:
    account = FinancialAccountService(session).create(
        user_id=current_user.id,
        name=request.name,
        account_type=request.account_type,
        currency=request.currency,
        initial_balance=request.initial_balance,
        is_liquid=request.is_liquid,
    )
    return AccountResponse.model_validate(account)


@router.get("", response_model=list[AccountResponse])
def list_accounts(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> list[AccountResponse]:
    accounts = FinancialAccountService(session).list_active(current_user.id)
    return [AccountResponse.model_validate(account) for account in accounts]


@router.get("/{account_id}", response_model=AccountResponse)
def read_account(
    account_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> AccountResponse:
    try:
        account = FinancialAccountService(session).get_active(
            current_user.id, account_id
        )
    except AccountNotFoundError as exc:
        raise _account_not_found() from exc
    return AccountResponse.model_validate(account)


@router.patch("/{account_id}/balance", response_model=AccountResponse)
def update_account_balance(
    account_id: UUID,
    request: AccountBalanceUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> AccountResponse:
    try:
        account = FinancialAccountService(session).update_balance(
            user_id=current_user.id, account_id=account_id, balance=request.balance
        )
    except AccountNotFoundError as exc:
        raise _account_not_found() from exc
    return AccountResponse.model_validate(account)


@router.get(
    "/{account_id}/balance-history", response_model=list[AccountBalanceSnapshotResponse]
)
def read_account_balance_history(
    account_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AccountBalanceSnapshotResponse]:
    try:
        snapshots = FinancialAccountService(session).list_balance_history(
            user_id=current_user.id, account_id=account_id, limit=limit, offset=offset
        )
    except AccountNotFoundError as exc:
        raise _account_not_found() from exc
    return [AccountBalanceSnapshotResponse.model_validate(item) for item in snapshots]


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_account(
    account_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> Response:
    try:
        FinancialAccountService(session).archive(
            user_id=current_user.id, account_id=account_id
        )
    except AccountNotFoundError as exc:
        raise _account_not_found() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _account_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
    )
