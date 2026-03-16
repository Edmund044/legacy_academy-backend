import uuid, enum
from datetime import datetime, date
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum, ForeignKey, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class PartnerStatus(str, enum.Enum):
    active = "active"; renewal_pending = "renewal_pending"; terminated = "terminated"; prospect = "prospect"

class ContractStatus(str, enum.Enum):
    draft = "draft"; active = "active"; renewal_pending = "renewal_pending"; expired = "expired"; terminated = "terminated"

class PaymentCycle(str, enum.Enum):
    monthly = "monthly"; quarterly = "quarterly"; biannual = "biannual"; annual = "annual"


class SchoolPartner(Base):
    __tablename__ = "school_partners"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[PartnerStatus] = mapped_column(Enum(PartnerStatus), nullable=False, default=PartnerStatus.prospect, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    contracts = relationship("Contract", back_populates="school_partner")


class Contract(Base):
    __tablename__ = "contracts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("school_partners.id"), nullable=False, index=True)
    contract_ref: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    base_rate_per_student_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    enrollment_cap: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_cycle: Mapped[PaymentCycle] = mapped_column(Enum(PaymentCycle), nullable=False)
    termination_notice_days: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=90)
    renewal_date: Mapped[date | None] = mapped_column(Date, index=True)
    status: Mapped[ContractStatus] = mapped_column(Enum(ContractStatus), nullable=False, default=ContractStatus.draft, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    school_partner = relationship("SchoolPartner", back_populates="contracts")
    revenue_splits = relationship("RevSplitContract", back_populates="contract")
    audit_entries = relationship("ContractAudit", back_populates="contract")
    coach_allocations = relationship("CoachAllocation", back_populates="contract")


class RevSplitContract(Base):
    __tablename__ = "rev_split_c"
    __table_args__ = (CheckConstraint("school_pct + ops_pct + provider_pct = 100", name="chk_rev_split_c"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    school_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    ops_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    provider_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    restructuring_fee_usd: Mapped[float | None] = mapped_column(Numeric(10, 2))
    is_simulation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    projected_annual_usd: Mapped[float | None] = mapped_column(Numeric(12, 2))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    contract = relationship("Contract", back_populates="revenue_splits")


class ContractAudit(Base):
    __tablename__ = "contract_audit"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    contract = relationship("Contract", back_populates="audit_entries")


class CoachAllocation(Base):
    __tablename__ = "coach_allocations"
    __table_args__ = (UniqueConstraint("contract_id", "coach_id", name="uq_contract_coach"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    coach_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("coaches.id"), nullable=False, index=True)
    allocation_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    contract = relationship("Contract", back_populates="coach_allocations")
    coach = relationship("Coach", back_populates="coach_allocations")
