import uuid, enum
from datetime import datetime, date
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class DisbCategory(str, enum.Enum):
    school_fees = "school_fees"; equipment = "equipment"; transport = "transport"
    medical = "medical"; nutrition = "nutrition"; accommodation = "accommodation"

class CaseStatus(str, enum.Enum):
    active = "active"; suspended = "suspended"; completed = "completed"; cancelled = "cancelled"

class FeeStatus(str, enum.Enum):
    pending = "pending"; paid = "paid"; overdue = "overdue"; waived = "waived"


class Disbursement(Base):
    __tablename__ = "disbursements"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    category: Mapped[DisbCategory] = mapped_column(Enum(DisbCategory), nullable=False, index=True)
    amount_kes: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    disbursed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    disbursed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    player = relationship("Player", back_populates="disbursements")


class SponsorshipCase(Base):
    __tablename__ = "sponsorship_cases"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    case_ref: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    sponsor_name: Mapped[str] = mapped_column(String(200), nullable=False)
    annual_budget_kes: Mapped[int] = mapped_column(Integer, nullable=False)
    total_spent_kes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[CaseStatus] = mapped_column(Enum(CaseStatus), nullable=False, default=CaseStatus.active, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    player = relationship("Player", back_populates="sponsorship_cases")
    costs = relationship("CaseCost", back_populates="case_obj")
    receipts = relationship("CaseReceipt", back_populates="case_obj")
    notes = relationship("CaseNote", back_populates="case_obj")
    school_fee_payments = relationship("SchoolFeePayment", back_populates="case_obj")

    @property
    def remaining_kes(self) -> int:
        return self.annual_budget_kes - self.total_spent_kes


class CaseCost(Base):
    __tablename__ = "case_costs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sponsorship_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    cost_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount_kes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    case_obj = relationship("SponsorshipCase", back_populates="costs")


class CaseReceipt(Base):
    __tablename__ = "case_receipts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sponsorship_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    case_obj = relationship("SponsorshipCase", back_populates="receipts")


class CaseNote(Base):
    __tablename__ = "case_notes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sponsorship_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    case_obj = relationship("SponsorshipCase", back_populates="notes")


class SchoolFeePayment(Base):
    __tablename__ = "school_fee_pmts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sponsorship_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    term: Mapped[str] = mapped_column(String(50), nullable=False)
    amount_kes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[FeeStatus] = mapped_column(Enum(FeeStatus), nullable=False, default=FeeStatus.pending)
    due_date: Mapped[date | None] = mapped_column(Date)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    case_obj = relationship("SponsorshipCase", back_populates="school_fee_payments")
