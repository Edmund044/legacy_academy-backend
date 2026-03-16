import uuid, enum
from datetime import datetime, date
from sqlalchemy import Date, DateTime, Enum, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class TournamentFormat(str, enum.Enum):
    league = "league"; knockout = "knockout"; group_stage = "group_stage"
    friendly = "friendly"; round_robin = "round_robin"

class TournamentStatus(str, enum.Enum):
    planned = "planned"; active = "active"; completed = "completed"; cancelled = "cancelled"

class MatchStatus(str, enum.Enum):
    scheduled = "scheduled"; live = "live"; completed = "completed"
    postponed = "postponed"; cancelled = "cancelled"


class Tournament(Base):
    __tablename__ = "tournaments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    age_group: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    format: Mapped[TournamentFormat] = mapped_column(Enum(TournamentFormat), nullable=False)
    status: Mapped[TournamentStatus] = mapped_column(Enum(TournamentStatus), nullable=False, default=TournamentStatus.planned, index=True)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    teams = relationship("TournamentTeam", back_populates="tournament")
    matches = relationship("Match", back_populates="tournament")


class TournamentTeam(Base):
    __tablename__ = "tournament_teams"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("academy_groups.id"))
    team_name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_opponent: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    tournament = relationship("Tournament", back_populates="teams")
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")


class Match(Base):
    __tablename__ = "matches"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True)
    home_team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tournament_teams.id"), nullable=False)
    away_team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tournament_teams.id"), nullable=False)
    venue_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("venues.id"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    home_score: Mapped[int | None] = mapped_column(SmallInteger)
    away_score: Mapped[int | None] = mapped_column(SmallInteger)
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), nullable=False, default=MatchStatus.scheduled, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    tournament = relationship("Tournament", back_populates="matches")
    home_team = relationship("TournamentTeam", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("TournamentTeam", foreign_keys=[away_team_id], back_populates="away_matches")
    venue = relationship("Venue", back_populates="matches")
