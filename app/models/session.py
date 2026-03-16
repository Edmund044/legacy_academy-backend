import uuid, enum
from datetime import datetime, date, time
from sqlalchemy import (Boolean, Date, DateTime, Enum, ForeignKey, Integer,
                        Numeric, SmallInteger, String, Text, Time, UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class SessionStatus(str, enum.Enum):
    planned = "planned"; active = "active"; completed = "completed"; cancelled = "cancelled"

class EnrollStatus(str, enum.Enum):
    enrolled = "enrolled"; attended = "attended"; absent = "absent"; cancelled = "cancelled"

class BillingMethod(str, enum.Enum):
    annual_subscription = "annual_subscription"; pay_as_you_go = "pay_as_you_go"
    scholarship = "scholarship"; sponsored = "sponsored"

class DrillIntensity(str, enum.Enum):
    low = "low"; medium = "medium"; high = "high"; elite = "elite"


class Venue(Base):
    __tablename__ = "venues"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campus_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campuses.id"))
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer)
    pitch_count: Mapped[int | None] = mapped_column(SmallInteger)
    location: Mapped[str | None] = mapped_column(Text)
    sessions = relationship("Session", back_populates="venue")
    matches = relationship("Match", back_populates="venue")


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    coach_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("coaches.id"), nullable=False, index=True)
    venue_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("venues.id"))
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    enrollment_cap: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=30)
    revenue_kes: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), nullable=False, default=SessionStatus.planned, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    coach = relationship("Coach", back_populates="sessions")
    venue = relationship("Venue", back_populates="sessions")
    enrollments = relationship("SessionEnrollment", back_populates="session")
    plan = relationship("SessionPlan", back_populates="session", uselist=False)
    staff = relationship("SessionStaff", back_populates="session")
    handovers = relationship("EquipmentHandover", back_populates="session")
    revenue_split = relationship("RevenueSplit", back_populates="session", uselist=False)


class SessionEnrollment(Base):
    __tablename__ = "session_enrollments"
    __table_args__ = (UniqueConstraint("session_id", "player_id", name="uq_session_player"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    billing_method: Mapped[BillingMethod] = mapped_column(Enum(BillingMethod), nullable=False)
    player_eligibility: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[EnrollStatus] = mapped_column(Enum(EnrollStatus), nullable=False, default=EnrollStatus.enrolled)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    session = relationship("Session", back_populates="enrollments")
    player = relationship("Player", back_populates="enrollments")
    attendance_billings = relationship("AttendanceBilling", back_populates="enrollment")


class Drill(Base):
    __tablename__ = "drills"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    duration_min: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=15)
    intensity: Mapped[DrillIntensity] = mapped_column(Enum(DrillIntensity), nullable=False, default=DrillIntensity.medium)
    description: Mapped[str | None] = mapped_column(Text)
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    plan_drills = relationship("SessionPlanDrill", back_populates="drill")


class SessionPlan(Base):
    __tablename__ = "session_plans"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), unique=True, nullable=False)
    objectives: Mapped[str | None] = mapped_column(Text)
    goals: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    session = relationship("Session", back_populates="plan")
    drills = relationship("SessionPlanDrill", back_populates="plan", order_by="SessionPlanDrill.order_idx")


class SessionPlanDrill(Base):
    __tablename__ = "session_plan_drills"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("session_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    drill_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("drills.id"), nullable=False)
    order_idx: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    coaching_points: Mapped[str | None] = mapped_column(Text)
    duration_override: Mapped[int | None] = mapped_column(SmallInteger)
    plan = relationship("SessionPlan", back_populates="drills")
    drill = relationship("Drill", back_populates="plan_drills")


class SessionStaff(Base):
    __tablename__ = "session_staff"
    __table_args__ = (UniqueConstraint("session_id", "coach_id", name="uq_session_coach"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    coach_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("coaches.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(80), nullable=False, default="assistant")
    session = relationship("Session", back_populates="staff")
    coach = relationship("Coach", back_populates="session_staff")
