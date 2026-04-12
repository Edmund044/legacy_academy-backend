from sqlalchemy import  String, Float, DateTime, ForeignKey, Enum, Text, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from app.models.user import User
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.base import Base


def gen_uuid():
    return str(uuid.uuid4())


class AccountType(str, enum.Enum):
    SAVINGS = "savings"
    CURRENT = "current"
    LOAN = "loan"


class TransactionType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class TransactionCategory(str, enum.Enum):
    TOP_UP = "top_up"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    LOAN_DISBURSEMENT = "loan_disbursement"
    LOAN_REPAYMENT = "loan_repayment"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    FEE = "fee"
    INTEREST = "interest"


class LoanStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    CLOSED = "closed"
    REJECTED = "rejected"



class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_number: Mapped[int] = mapped_column(String, unique=True, nullable=False, index=True)
    account_type: Mapped[str] = mapped_column(Enum(AccountType), nullable=False)
    balance: Mapped[int] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String, default="KES")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="accounts")
    transactions_sent = relationship("Transaction", foreign_keys="Transaction.from_account_id", back_populates="from_account")
    transactions_received = relationship("Transaction", foreign_keys="Transaction.to_account_id", back_populates="to_account")
    loans = relationship("Loan", back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    reference: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(Enum(TransactionType), nullable=False)
    category: Mapped[str] = mapped_column(Enum(TransactionCategory), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    balance_before: Mapped[float] = mapped_column(Float, nullable=False)
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="success")
    from_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    to_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    from_account = relationship("Account", foreign_keys=[from_account_id], back_populates="transactions_sent")
    to_account = relationship("Account", foreign_keys=[to_account_id], back_populates="transactions_received")


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[uuid.UUID] = mapped_column(String, primary_key=True, default=gen_uuid)
    account_id: Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    principal: Mapped[float]  = mapped_column(Float, nullable=False)
    interest_rate: Mapped[int]  = mapped_column(Float, nullable=False)  # annual %
    duration_months: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_payment: Mapped[float] = mapped_column(Float, nullable=False)
    total_repayable: Mapped[float] = mapped_column(Float, nullable=False)
    amount_repaid: Mapped[float] = mapped_column(Float, default=0.0)
    outstanding_balance: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(Enum(LoanStatus), default=LoanStatus.PENDING)
    purpose: Mapped[float] = mapped_column(String, nullable=True)
    disbursed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="loans")
