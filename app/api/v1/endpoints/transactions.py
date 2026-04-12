from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.deps import get_db,get_current_active_user
from app.models.banking import TransactionCategory, TransactionType, LoanStatus
from app.schemas.schemas import TopUpRequest, WithdrawalRequest, TransferRequest, TransactionOut
from app.services import banking

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/top-up", response_model=TransactionOut, status_code=201)
async def top_up(
    payload: TopUpRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Credit an account via top-up (e.g. M-Pesa, bank transfer in)."""
    return await banking.top_up(
        db=db,
        account_id=payload.account_id,
        amount=payload.amount,
        user_id=current_user.id,
        description=payload.description,
    )


@router.post("/withdraw", response_model=TransactionOut, status_code=201)
async def withdraw(
    payload: WithdrawalRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Debit an account (cash withdrawal)."""
    return await banking.withdraw(
        db=db,
        account_id=payload.account_id,
        amount=payload.amount,
        user_id=current_user.id,
        description=payload.description,
    )


@router.post("/transfer", response_model=TransactionOut, status_code=201)
async def transfer(
    payload: TransferRequest,
    db: AsyncSession = Depends(get_db),
    current_user= Depends(get_current_active_user),
):
    """Transfer funds between accounts. A 0.5% fee (max KES 300) is applied."""
    return await banking.transfer(
        db=db,
        from_account_id=payload.from_account_id,
        to_account_number=payload.to_account_number,
        amount=payload.amount,
        user_id=current_user.id,
        description=payload.description,
    )


@router.get("/statement", response_model=List[TransactionOut])
async def get_statement(
    account_id: str = Query(...),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    category: Optional[TransactionCategory] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Paginated transaction statement with optional category filter."""
    return await banking.get_statement(
        db=db,
        account_id=account_id,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        category=category,
    )
