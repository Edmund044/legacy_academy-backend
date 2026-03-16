import uuid, enum
from datetime import datetime, date
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class PlayerStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"
    trialist = "trialist"
    graduated = "graduated"


class Campus(Base):
    __tablename__ = "campuses"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    location: Mapped[str] = mapped_column(Text, nullable=False)
    pitch_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    coaches = relationship("Coach", back_populates="campus")
    groups = relationship("AcademyGroup", back_populates="campus")


class Coach(Base):
    __tablename__ = "coaches"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    campus_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campuses.id"))
    license: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text)
    experience_years: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    rating: Mapped[float | None] = mapped_column(Numeric(3, 2))
    speciality: Mapped[str | None] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="coach_profile")
    campus = relationship("Campus", back_populates="coaches")
    assigned_groups = relationship("AcademyGroup", back_populates="coach")
    sessions = relationship("Session", back_populates="coach")
    session_staff = relationship("SessionStaff", back_populates="coach")
    equipment_handovers = relationship("EquipmentHandover", back_populates="coach")
    coach_liabilities = relationship("CoachLiability", back_populates="coach")
    revenue_splits = relationship("RevenueSplit", back_populates="coach")
    coach_allocations = relationship("CoachAllocation", back_populates="coach")


class AcademyGroup(Base):
    __tablename__ = "academy_groups"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age_group: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    division: Mapped[str | None] = mapped_column(String(100))
    coach_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("coaches.id"))
    campus_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campuses.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    coach = relationship("Coach", back_populates="assigned_groups")
    campus = relationship("Campus", back_populates="groups")
    players = relationship("Player", back_populates="group")


class Player(Base):
    __tablename__ = "players"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    group_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("academy_groups.id"), index=True)
    campus_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campuses.id"))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    position: Mapped[str | None] = mapped_column(String(60))
    status: Mapped[PlayerStatus] = mapped_column(Enum(PlayerStatus), nullable=False, default=PlayerStatus.active, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    group = relationship("AcademyGroup", back_populates="players")
    guardians = relationship("Guardian", back_populates="player")
    enrollments = relationship("SessionEnrollment", back_populates="player")
    subscriptions = relationship("Subscription", back_populates="player")
    stats = relationship("PlayerStat", back_populates="player")
    physical_assessments = relationship("PlayerPhysical", back_populates="player")
    injuries = relationship("PlayerInjury", back_populates="player")
    dev_timeline = relationship("DevTimeline", back_populates="player")
    video_highlights = relationship("VideoHighlight", back_populates="player")
    disbursements = relationship("Disbursement", back_populates="player")
    sponsorship_cases = relationship("SponsorshipCase", back_populates="player")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Guardian(Base):
    __tablename__ = "guardians"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(60), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    user = relationship("User", back_populates="guardian_profiles")
    player = relationship("Player", back_populates="guardians")
    invoices = relationship("Invoice", back_populates="guardian")
