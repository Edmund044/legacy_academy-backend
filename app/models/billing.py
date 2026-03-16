import uuid, enum
from datetime import datetime, date
from sqlalchemy import (Boolean, CheckConstraint, Date, DateTime, Enum, ForeignKey,
                        Integer, Numeric, String, func)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class SubPlan(str, enum.Enum):
    annual_elite = "annual_elite"; annual_standard = "annual_standard"
    sibling_discount = "sibling_discount"; scholarship = "scholarship"

class SubStatus(str, enum.Enum):
    active = "active"; expired = "expired"; suspended = "suspended"; pending_renewal = "pending_renewal"

class BillingStatus(str, enum.Enum):
    pending = "pending"; paid = "paid"; failed = "failed"; waived = "waived"

class InvoiceStatus(str, enum.Enum):
    draft = "draft"; issued = "issued"; paid = "paid"; overdue = "overdue"; void = "void"

class PayoutStatus(str, enum.Enum):
    pending = "pending"; reconciled = "reconciled"; paid = "paid"; disputed = "disputed"

class PaymentMethod(str, enum.Enum):
    mpesa = "mpesa"; card = "card"; bank_transfer = "bank_transfer"
    cash = "cash"; scholarship_credit = "scholarship_credit"

class PaymentStatus(str, enum.Enum):
    pending = "pending"; completed = "completed"; failed = "failed"; refunded = "refunded"


class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    plan_type: Mapped[SubPlan] = mapped_column(Enum(SubPlan), nullable=False)
    annual_fee_kes: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    scholarship_applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[SubStatus] = mapped_column(Enum(SubStatus), nullable=False, default=SubStatus.active, index=True)
    renewal_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    player = relationship("Player", back_populates="subscriptions")

    @property
    def net_fee_kes(self) -> int:
        return 0 if self.scholarship_applied else int(self.annual_fee_kes * (1 - self.discount_pct / 100))


class AttendanceBilling(Base):
    __tablename__ = "attendance_billing"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("session_enrollments.id"), nullable=False, index=True)
    cycle_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    charge_kes: Mapped[int] = mapped_column(Integer, nullable=False)
    billing_status: Mapped[BillingStatus] = mapped_column(Enum(BillingStatus), nullable=False, default=BillingStatus.pending, index=True)
    auto_trigger: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    enrollment = relationship("SessionEnrollment", back_populates="attendance_billings")


class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guardian_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guardians.id"), nullable=False, index=True)
    ref: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    total_kes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.draft, index=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    guardian = relationship("Guardian", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice")


class RevenueSplit(Base):
    __tablename__ = "revenue_splits"
    __table_args__ = (CheckConstraint("coach_pct + academy_pct = 100", name="chk_split_total"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"), unique=True, nullable=False)
    coach_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("coaches.id"), nullable=False, index=True)
    session_rate_kes: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    coach_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=60)
    academy_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=40)
    coach_amount_kes: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    academy_amount_kes: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    payout_status: Mapped[PayoutStatus] = mapped_column(Enum(PayoutStatus), nullable=False, default=PayoutStatus.pending, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    session = relationship("Session", back_populates="revenue_split")
    coach = relationship("Coach", back_populates="revenue_splits")


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"))
    amount_kes: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    provider_ref: Mapped[str | None] = mapped_column(String(100), unique=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.pending, index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    payer = relationship("User", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments")
