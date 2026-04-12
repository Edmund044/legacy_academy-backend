from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.deps import get_db,get_current_active_user
from app.models.user import User
from app.schemas.schemas import LoanApplication, LoanApproval, LoanRepayment, LoanOut
from app.services import banking

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post("/apply", response_model=LoanOut, status_code=201)
async def apply_for_loan(
    payload: LoanApplication,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Submit a loan application. Starts in PENDING state."""
    return await banking.apply_loan(
        db=db,
        account_id=payload.account_id,
        principal=payload.principal,
        duration_months=payload.duration_months,
        purpose=payload.purpose,
        user_id=current_user.id,
    )


@router.post("/{loan_id}/approve", response_model=LoanOut)
async def approve_loan(
    loan_id: str,
    payload: LoanApproval,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Approve a pending loan with a specific interest rate (annual %).
    In production this would be an admin-only endpoint.
    Sets monthly_payment and total_repayable using reducing-balance formula.
    """
    return await banking.approve_loan(db=db, loan_id=loan_id, interest_rate=payload.interest_rate)


@router.post("/{loan_id}/disburse", response_model=LoanOut)
async def disburse_loan(
    loan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Disburse an approved loan — credits the principal to the linked account.
    Loan moves to ACTIVE status.
    """
    return await banking.disburse_loan(db=db, loan_id=loan_id)


@router.post("/repay", response_model=LoanOut)
async def repay_loan(
    payload: LoanRepayment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Make a repayment toward an active loan.
    Debits the specified account. Loan auto-closes when fully repaid.
    """
    return await banking.repay_loan(
        db=db,
        loan_id=payload.loan_id,
        account_id=payload.account_id,
        amount=payload.amount,
        user_id=current_user.id,
    )


@router.get("/", response_model=List[LoanOut])
async def my_loans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all loans across the current user's accounts."""
    return await banking.get_user_loans(db=db, user_id=current_user.id)
