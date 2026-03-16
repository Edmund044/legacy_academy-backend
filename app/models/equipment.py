import uuid, enum
from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Integer, Numeric, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class EquipCategory(str, enum.Enum):
    balls = "balls"; training_gear = "training_gear"; field_equipment = "field_equipment"
    medical_kits = "medical_kits"; goalkeeping = "goalkeeping"; protective = "protective"

class EquipCondition(str, enum.Enum):
    excellent = "excellent"; good = "good"; fair = "fair"
    needs_repair = "needs_repair"; condemned = "condemned"

class HandoverStatus(str, enum.Enum):
    checked_out = "checked_out"; returned = "returned"; overdue = "overdue"


class EquipmentItem(Base):
    __tablename__ = "equipment_items"
    __table_args__ = (CheckConstraint("stock_assigned <= stock_total", name="chk_stock_valid"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campus_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campuses.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[EquipCategory] = mapped_column(Enum(EquipCategory), nullable=False, index=True)
    sku: Mapped[str | None] = mapped_column(String(80), unique=True)
    stock_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_assigned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    condition: Mapped[EquipCondition] = mapped_column(Enum(EquipCondition), nullable=False, default=EquipCondition.good)
    replacement_cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    handover_items = relationship("HandoverItem", back_populates="equipment")

    @property
    def utilization_pct(self) -> float:
        return round(self.stock_assigned / self.stock_total * 100, 1) if self.stock_total else 0.0


class EquipmentHandover(Base):
    __tablename__ = "equipment_handovers"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    coach_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("coaches.id"), nullable=False, index=True)
    checked_out_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[HandoverStatus] = mapped_column(Enum(HandoverStatus), nullable=False, default=HandoverStatus.checked_out, index=True)
    damage_notes: Mapped[str | None] = mapped_column(Text)
    coach = relationship("Coach", back_populates="equipment_handovers")
    session = relationship("Session", back_populates="handovers")
    items = relationship("HandoverItem", back_populates="handover")
    liabilities = relationship("CoachLiability", back_populates="handover")


class HandoverItem(Base):
    __tablename__ = "handover_items"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    handover_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("equipment_handovers.id", ondelete="CASCADE"), nullable=False, index=True)
    equipment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("equipment_items.id"), nullable=False)
    qty: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    condition_out: Mapped[EquipCondition] = mapped_column(Enum(EquipCondition), nullable=False)
    condition_in: Mapped[EquipCondition | None] = mapped_column(Enum(EquipCondition))
    is_lost: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_damaged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    handover = relationship("EquipmentHandover", back_populates="items")
    equipment = relationship("EquipmentItem", back_populates="handover_items")


class CoachLiability(Base):
    __tablename__ = "coach_liabilities"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coach_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("coaches.id"), nullable=False, index=True)
    handover_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("equipment_handovers.id"), nullable=False)
    amount_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_settled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    coach = relationship("Coach", back_populates="coach_liabilities")
    handover = relationship("EquipmentHandover", back_populates="liabilities")
