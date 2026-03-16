"""Tournaments: CRUD, teams, matches, score update."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_active_user, AdminOrCoach, Pagination
from app.core.responses import ok, paginated
from app.models.tournament import Tournament, TournamentTeam, Match, MatchStatus
from app.schemas.schemas import TournamentCreate, TournamentUpdate, TeamCreate, MatchCreate, MatchScoreUpdate

router = APIRouter(prefix="/tournaments", tags=["Tournaments"])


async def _get_tournament(tid: UUID, db: AsyncSession) -> Tournament:
    t = (await db.execute(select(Tournament).where(Tournament.id == tid))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Tournament not found"})
    return t


@router.get("", summary="List tournaments")
async def list_tournaments(pg: Pagination = Depends(), age_group: str | None = None,
                           db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    q = select(Tournament)
    if age_group:
        q = q.where(Tournament.age_group == age_group)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    return paginated([{
        "id": str(t.id), "name": t.name, "age_group": t.age_group,
        "format": t.format.value, "status": t.status.value,
        "start_date": t.start_date.isoformat() if t.start_date else None,
        "end_date": t.end_date.isoformat() if t.end_date else None,
    } for t in rows], total, pg.page, pg.per_page)


@router.post("", status_code=201, summary="Create tournament")
async def create_tournament(body: TournamentCreate, db: AsyncSession = Depends(get_db), _=Depends(AdminOrCoach)):
    t = Tournament(**body.model_dump())
    db.add(t)
    await db.flush()
    return ok({"id": str(t.id), "name": t.name, "format": t.format.value})


@router.get("/{tournament_id}", summary="Get tournament details")
async def get_tournament(tournament_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    t = await _get_tournament(tournament_id, db)
    await db.refresh(t, ["teams", "matches"])
    return ok({
        "id": str(t.id), "name": t.name, "age_group": t.age_group,
        "format": t.format.value, "status": t.status.value,
        "description": t.description,
        "start_date": t.start_date.isoformat() if t.start_date else None,
        "end_date": t.end_date.isoformat() if t.end_date else None,
        "team_count": len(t.teams), "match_count": len(t.matches),
    })


@router.patch("/{tournament_id}", summary="Update tournament")
async def update_tournament(tournament_id: UUID, body: TournamentUpdate,
                            db: AsyncSession = Depends(get_db), _=Depends(AdminOrCoach)):
    t = await _get_tournament(tournament_id, db)
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(t, f, v)
    await db.flush()
    return ok({"id": str(t.id), "status": t.status.value})


@router.delete("/{tournament_id}", status_code=204, summary="Cancel tournament")
async def delete_tournament(tournament_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOrCoach)):
    t = await _get_tournament(tournament_id, db)
    t.status = "cancelled"
    await db.flush()


@router.get("/{tournament_id}/teams", summary="List tournament teams")
async def list_teams(tournament_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    await _get_tournament(tournament_id, db)
    rows = (await db.execute(
        select(TournamentTeam).where(TournamentTeam.tournament_id == tournament_id)
    )).scalars().all()
    return ok([{
        "id": str(t.id), "team_name": t.team_name,
        "is_opponent": t.is_opponent,
        "group_id": str(t.group_id) if t.group_id else None,
    } for t in rows])


@router.post("/{tournament_id}/teams", status_code=201, summary="Add team to tournament")
async def add_team(tournament_id: UUID, body: TeamCreate,
                   db: AsyncSession = Depends(get_db), _=Depends(AdminOrCoach)):
    await _get_tournament(tournament_id, db)
    team = TournamentTeam(tournament_id=tournament_id, **body.model_dump())
    db.add(team)
    await db.flush()
    return ok({"team_id": str(team.id), "team_name": team.team_name})


@router.get("/{tournament_id}/matches", summary="List tournament matches")
async def list_matches(tournament_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    await _get_tournament(tournament_id, db)
    rows = (await db.execute(
        select(Match).where(Match.tournament_id == tournament_id).order_by(Match.scheduled_at)
    )).scalars().all()
    return ok([{
        "id": str(m.id), "scheduled_at": m.scheduled_at.isoformat(),
        "home_team_id": str(m.home_team_id), "away_team_id": str(m.away_team_id),
        "home_score": m.home_score, "away_score": m.away_score, "status": m.status.value,
    } for m in rows])


@router.post("/{tournament_id}/matches", status_code=201, summary="Schedule match")
async def create_match(tournament_id: UUID, body: MatchCreate,
                       db: AsyncSession = Depends(get_db), _=Depends(AdminOrCoach)):
    await _get_tournament(tournament_id, db)
    m = Match(tournament_id=tournament_id, **body.model_dump())
    db.add(m)
    await db.flush()
    return ok({"match_id": str(m.id), "scheduled_at": m.scheduled_at.isoformat()})


@router.patch("/matches/{match_id}/score", summary="Update match score")
async def update_score(match_id: UUID, body: MatchScoreUpdate,
                       db: AsyncSession = Depends(get_db), _=Depends(AdminOrCoach)):
    m = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not m:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Match not found"})
    m.home_score = body.home_score
    m.away_score = body.away_score
    if body.status:
        m.status = body.status
    await db.flush()
    return ok({"match_id": str(m.id), "home_score": m.home_score, "away_score": m.away_score, "status": m.status.value})
