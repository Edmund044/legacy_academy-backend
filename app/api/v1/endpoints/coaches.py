"""Coaches: CRUD + sessions sub-resource + revenue + schedule."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import json
from app.core.deps import get_db, get_current_active_user, AdminOnly, AdminOrCoach, Pagination
from app.core.responses import ok, paginated
from app.models.people import Coach
from app.models.session import Session
from app.schemas.schemas import CoachCreate, CoachUpdate, CoachOut

router = APIRouter(prefix="/coaches", tags=["Coaches"])


async def _get_coach(coach_id: UUID, db: AsyncSession) -> Coach:
    coach = (await db.execute(
        select(Coach).where(Coach.id == coach_id)
    )).scalar_one_or_none()
    if not coach:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Coach not found"})
    return coach


@router.get("", summary="List coaches")
async def list_coaches(
    pg: Pagination = Depends(),
    campus_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    # _=Depends(get_current_active_user),
):
    q = select(Coach)
    if campus_id:
        q = q.where(Coach.campus_id == campus_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    data = []
    for c in rows:
        # await db.refresh(c, ["user"])
        data.append({
            "id": str(c.id), "license": c.license, "experience_years": c.experience_years,
            "rating": float(c.rating) if c.rating else None, "speciality": c.speciality,
            "name": c.full_name,
            "campus_id": str(c.campus_id) if c.campus_id else None,
            "bio": c.bio,
            "role": c.speciality,
            "stats": {
                "experience": c.experience_years,
                "teams": len(c.primary_assigned_teams.split(",")) if c.primary_assigned_teams else 0,
                "win_rate": float(c.career_win_rate) if c.career_win_rate else None,
            },
            "teams": c.primary_assigned_teams.split(",") if c.primary_assigned_teams else [],
            "skills": c.speciality.split(",") if c.speciality else [],
        })
    return paginated(data, total, pg.page, pg.per_page)


@router.post("", status_code=201, summary="Create coach profile (admin)")
async def create_coach(body: CoachCreate, db: AsyncSession = Depends(get_db)
                    #    , _=Depends(AdminOnly)
                       ):
    coach = Coach(**body.model_dump(exclude={"primary_assigned_teams"}), primary_assigned_teams=json.dumps(body.primary_assigned_teams) if body.primary_assigned_teams else None)
    db.add(coach)
    await db.flush()
    # await db.refresh(coach, ["user"])
    return ok({"id": str(coach.id), "license": coach.license, "experience_years": coach.experience_years, "rating": float(coach.rating) if coach.rating else None,})


@router.get("/{coach_id}", summary="Get coach profile")
async def get_coach(coach_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    c = await _get_coach(coach_id, db)
    await db.refresh(c, ["user", "campus"])
    return ok({
        "id": str(c.id), "license": c.license, "bio": c.bio,
        "experience_years": c.experience_years, "rating": float(c.rating) if c.rating else None,
        "speciality": c.speciality, "created_at": c.created_at.isoformat(),
        "user": {"id": str(c.user.id), "email": c.user.email,
                 "first_name": c.user.first_name, "last_name": c.user.last_name},
        "campus": {"id": str(c.campus.id), "name": c.campus.name} if c.campus else None,
    })


@router.patch("/{coach_id}", summary="Update coach profile")
async def update_coach(
    coach_id: UUID,
    body: CoachUpdate,
    db: AsyncSession = Depends(get_db),
    # _=Depends(AdminOrCoach),
):
    c = await _get_coach(coach_id, db)
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(c, field, val)
    await db.flush()
    return ok({"id": str(c.id), "message": "Coach updated"})


@router.delete("/{coach_id}", status_code=204, summary="Delete coach (admin)")
async def delete_coach(coach_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
    c = await _get_coach(coach_id, db)
    await db.delete(c)


@router.get("/{coach_id}/sessions", summary="Coach's sessions")
async def coach_sessions(
    coach_id: UUID,
    pg: Pagination = Depends(),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    await _get_coach(coach_id, db)
    q = select(Session).where(Session.coach_id == coach_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.order_by(Session.session_date.desc()).offset(pg.offset).limit(pg.per_page))).scalars().all()
    data = [{"id": str(s.id), "name": s.name, "session_date": s.session_date.isoformat(),
             "status": s.status.value, "revenue_kes": float(s.revenue_kes)} for s in rows]
    return paginated(data, total, pg.page, pg.per_page)


@router.get("/{coach_id}/revenue", summary="Coach revenue summary")
async def coach_revenue(
    coach_id: UUID,
    from_: str = Query(None, alias="from"),
    to: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(AdminOrCoach),
):
    await _get_coach(coach_id, db)
    # TODO: aggregate from RevenueSplit for date range
    return ok({
        "coach_id": str(coach_id),
        "period": {"from": from_, "to": to},
        "total_sessions": 0,
        "gross_revenue_kes": 0,
        "coach_share_kes": 0,   # 60%
        "academy_share_kes": 0, # 40%
        "pending_payout_kes": 0,
    })


@router.get("/{coach_id}/schedule", summary="Coach weekly schedule")
async def coach_schedule(
    coach_id: UUID,
    week: str = Query(None, description="ISO week start date YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    await _get_coach(coach_id, db)
    # TODO: filter sessions by week
    return ok({"coach_id": str(coach_id), "week": week, "sessions": []})
