import uuid
import random
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from fastapi import HTTPException, status
from app.models.banking import TransactionCategory, TransactionType, Transaction,Account,AccountType



# ── Helpers ───────────────────────────────────────────────────────────────────

def gen_ref() -> str:
    return f"TXN{uuid.uuid4().hex[:12].upper()}"


def gen_account_number() -> str:
    return f"KE{random.randint(10_000_000_0000, 99_999_999_9999)}"


def calc_loan(principal: float, annual_rate: float, months: int):
    r = (annual_rate / 100) / 12
    if r == 0:
        monthly = principal / months
    else:
        monthly = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    total = monthly * months
    return round(monthly, 2), round(total, 2)


TRANSFER_FEE_RATE = 0.005  # 0.5%
MAX_TRANSFER_FEE = 300.0


# ── Account Service ───────────────────────────────────────────────────────────

async def create_account(db: AsyncSession, user_id: str, account_type: AccountType,
                         currency: str = "KES", initial_deposit: float = 0.0) -> Account:
    acc_no = gen_account_number()
    # ensure uniqueness
    while (await db.execute(select(Account).where(Account.account_number == acc_no))).scalar_one_or_none():
        acc_no = gen_account_number()

    account = Account(
        account_number=acc_no,
        account_type=account_type,
        balance=initial_deposit,
        currency=currency,
        user_id=user_id,
    )
    db.add(account)
    await db.flush()

    if
        await _record_transaction(
            db=db,
            tx_type=TransactionType.CREDIT,
            category=TransactionCategory.DEPOSIT,
            amount=initial_deposit,
            balance_before=0.0,
            balance_after=initial_deposit,
            to_account_id=account.id,
            description="Initial deposit",
        )
    await db.commit()
    await db.refresh(account)
    return account


# async def get_user_accounts(db: AsyncSession, user_id: str) -> List[Account]:
#     result = await db.execute(select(Account).where(Account.user_id == user_id))
#     return result.scalars().all()


# async def _get_account(db: AsyncSession, account_id: str, user_id: Optional[str] = None) -> Account:
#     q = select(Account).where(Account.id == account_id)
#     if user_id:
#         q = q.where(Account.user_id == user_id)
#     result = await db.execute(q)
#     account = result.scalar_one_or_none()
#     if not account:
#         raise HTTPException(status_code=404, detail="Account not found")
#     if not account.is_active:
#         raise HTTPException(status_code=400, detail="Account is inactive")
#     return account


async def _record_transaction(
    db: AsyncSession,
    tx_type: TransactionType,
    category: TransactionCategory,
    amount: float,
    balance_before: float,
    balance_after: float,
    from_account_id: Optional[str] = None,
    to_account_id: Optional[str] = None,
    description: Optional[str] = None,
    fee: float = 0.0,
) -> Transaction:
    tx = Transaction(
        reference=gen_ref(),
        transaction_type=tx_type,
        category=category,
        amount=amount,
        fee=fee,
        balance_before=balance_before,
        balance_after=balance_after,
        description=description,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
    )
    db.add(tx)
    await db.flush()
    return tx


# ── Top Up ────────────────────────────────────────────────────────────────────

# async def top_up(db: AsyncSession, account_id: str, amount: float,
#                  user_id: str, description: str = "Top up") -> Transaction:
#     account = await _get_account(db, account_id, user_id)
#     before = account.balance
#     account.balance = round(before + amount, 2)

#     tx = await _record_transaction(
#         db=db,
#         tx_type=TransactionType.CREDIT,
#         category=TransactionCategory.TOP_UP,
#         amount=amount,
#         balance_before=before,
#         balance_after=account.balance,
#         to_account_id=account.id,
#         description=description,
#     )
#     await db.commit()
#     await db.refresh(tx)
#     return tx


# ── Withdrawal ────────────────────────────────────────────────────────────────

# async def withdraw(db: AsyncSession, account_id: str, amount: float,
#                    user_id: str, description: str = "Withdrawal") -> Transaction:
#     account = await _get_account(db, account_id, user_id)
#     if account.balance < amount:
#         raise HTTPException(status_code=400, detail="Insufficient balance")

#     before = account.balance
#     account.balance = round(before - amount, 2)

#     tx = await _record_transaction(
#         db=db,
#         tx_type=TransactionType.DEBIT,
#         category=TransactionCategory.WITHDRAWAL,
#         amount=amount,
#         balance_before=before,
#         balance_after=account.balance,
#         from_account_id=account.id,
#         description=description,
#     )
#     await db.commit()
#     await db.refresh(tx)
#     return tx


# ── Transfer ──────────────────────────────────────────────────────────────────

# async def transfer(db: AsyncSession, from_account_id: str, to_account_number: str,
#                    amount: float, user_id: str, description: str = "Transfer"):
#     sender = await _get_account(db, from_account_id, user_id)

#     result = await db.execute(select(Account).where(Account.account_number == to_account_number))
#     recipient = result.scalar_one_or_none()
#     if not recipient:
#         raise HTTPException(status_code=404, detail="Recipient account not found")
#     if not recipient.is_active:
#         raise HTTPException(status_code=400, detail="Recipient account is inactive")
#     if sender.id == recipient.id:
#         raise HTTPException(status_code=400, detail="Cannot transfer to same account")

#     fee = min(round(amount * TRANSFER_FEE_RATE, 2), MAX_TRANSFER_FEE)
#     total_debit = amount + fee

#     if sender.balance < total_debit:
#         raise HTTPException(status_code=400, detail=f"Insufficient balance. Need {total_debit} (amount + {fee} fee)")

#     # Debit sender
#     sender_before = sender.balance
#     sender.balance = round(sender_before - total_debit, 2)
#     debit_tx = await _record_transaction(
#         db=db,
#         tx_type=TransactionType.DEBIT,
#         category=TransactionCategory.TRANSFER_OUT,
#         amount=amount,
#         fee=fee,
#         balance_before=sender_before,
#         balance_after=sender.balance,
#         from_account_id=sender.id,
#         to_account_id=recipient.id,
#         description=description,
#     )

#     # Credit recipient
#     recipient_before = recipient.balance
#     recipient.balance = round(recipient_before + amount, 2)
#     await _record_transaction(
#         db=db,
#         tx_type=TransactionType.CREDIT,
#         category=TransactionCategory.TRANSFER_IN,
#         amount=amount,
#         balance_before=recipient_before,
#         balance_after=recipient.balance,
#         from_account_id=sender.id,
#         to_account_id=recipient.id,
#         description=description,
#     )

#     await db.commit()
#     await db.refresh(debit_tx)
#     return debit_tx


# ── Loans ─────────────────────────────────────────────────────────────────────

# async def apply_loan(db: AsyncSession, account_id: str, principal: float,
#                      duration_months: int, purpose: Optional[str], user_id: str) -> Loan:
#     account = await _get_account(db, account_id, user_id)

#     # Placeholder interest — will be set on approval
#     loan = Loan(
#         account_id=account.id,
#         principal=principal,
#         interest_rate=0.0,
#         duration_months=duration_months,
#         monthly_payment=0.0,
#         total_repayable=principal,
#         outstanding_balance=principal,
#         status=LoanStatus.PENDING,
#         purpose=purpose,
#     )
#     db.add(loan)
#     await db.commit()
#     await db.refresh(loan)
#     return loan


# async def approve_loan(db: AsyncSession, loan_id: str, interest_rate: float) -> Loan:
#     result = await db.execute(select(Loan).where(Loan.id == loan_id))
#     loan = result.scalar_one_or_none()
#     if not loan:
#         raise HTTPException(status_code=404, detail="Loan not found")
#     if loan.status != LoanStatus.PENDING:
#         raise HTTPException(status_code=400, detail=f"Loan is already {loan.status}")

#     monthly, total = calc_loan(loan.principal, interest_rate, loan.duration_months)
#     loan.interest_rate = interest_rate
#     loan.monthly_payment = monthly
#     loan.total_repayable = total
#     loan.outstanding_balance = total
#     loan.status = LoanStatus.APPROVED

#     await db.commit()
#     await db.refresh(loan)
#     return loan


# async def disburse_loan(db: AsyncSession, loan_id: str) -> Loan:
#     result = await db.execute(select(Loan).where(Loan.id == loan_id))
#     loan = result.scalar_one_or_none()
#     if not loan:
#         raise HTTPException(status_code=404, detail="Loan not found")
#     if loan.status != LoanStatus.APPROVED:
#         raise HTTPException(status_code=400, detail="Loan must be approved before disbursement")

#     account = await _get_account(db, loan.account_id)
#     before = account.balance
#     account.balance = round(before + loan.principal, 2)
#     loan.status = LoanStatus.ACTIVE
#     loan.disbursed_at = datetime.utcnow()

#     await _record_transaction(
#         db=db,
#         tx_type=TransactionType.CREDIT,
#         category=TransactionCategory.LOAN_DISBURSEMENT,
#         amount=loan.principal,
#         balance_before=before,
#         balance_after=account.balance,
#         to_account_id=account.id,
#         description=f"Loan disbursement — Loan #{loan_id[:8]}",
#     )

#     await db.commit()
#     await db.refresh(loan)
#     return loan


# async def repay_loan(db: AsyncSession, loan_id: str, account_id: str,
#                      amount: float, user_id: str) -> Loan:
#     result = await db.execute(select(Loan).where(Loan.id == loan_id))
#     loan = result.scalar_one_or_none()
#     if not loan:
#         raise HTTPException(status_code=404, detail="Loan not found")
#     if loan.status != LoanStatus.ACTIVE:
#         raise HTTPException(status_code=400, detail="Loan is not active")

#     account = await _get_account(db, account_id, user_id)
#     if account.balance < amount:
#         raise HTTPException(status_code=400, detail="Insufficient balance for repayment")

#     repay_amount = min(amount, loan.outstanding_balance)

#     # Debit account
#     before = account.balance
#     account.balance = round(before - repay_amount, 2)

#     loan.amount_repaid = round(loan.amount_repaid + repay_amount, 2)
#     loan.outstanding_balance = round(loan.outstanding_balance - repay_amount, 2)

#     if loan.outstanding_balance <= 0:
#         loan.outstanding_balance = 0.0
#         loan.status = LoanStatus.CLOSED

#     await _record_transaction(
#         db=db,
#         tx_type=TransactionType.DEBIT,
#         category=TransactionCategory.LOAN_REPAYMENT,
#         amount=repay_amount,
#         balance_before=before,
#         balance_after=account.balance,
#         from_account_id=account.id,
#         description=f"Loan repayment — Loan #{loan_id[:8]}",
#     )

#     await db.commit()
#     await db.refresh(loan)
#     return loan


# ── Statement ─────────────────────────────────────────────────────────────────

# async def get_statement(db: AsyncSession, account_id: str, user_id: str,
#                         limit: int = 50, offset: int = 0,
#                         category: Optional[TransactionCategory] = None) -> List[Transaction]:
#     account = await _get_account(db, account_id, user_id)

#     q = select(Transaction).where(
#         or_(Transaction.from_account_id == account.id, Transaction.to_account_id == account.id)
#     )
#     if category:
#         q = q.where(Transaction.category == category)

#     q = q.order_by(Transaction.created_at.desc()).offset(offset).limit(limit)
#     result = await db.execute(q)
#     return result.scalars().all()


# async def get_user_loans(db: AsyncSession, user_id: str) -> List[Loan]:
#     # Get all account ids for user
#     acc_result = await db.execute(select(Account.id).where(Account.user_id == user_id))
#     account_ids = [row[0] for row in acc_result.fetchall()]
#     if not account_ids:
#         return []
#     result = await db.execute(select(Loan).where(Loan.account_id.in_(account_ids)))
#     return result.scalars().all()
