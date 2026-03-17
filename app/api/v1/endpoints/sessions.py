"""Sessions: CRUD + enroll, roster, checkin, revenue."""
from uuid import UUID
from datetime import date as dt_date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_active_user, AdminOrCoach, Pagination
from app.core.responses import ok, paginated
from app.models.session import Session, SessionEnrollment, EnrollStatus
from app.schemas.schemas import SessionCreate, SessionUpdate, EnrollIn, CheckInIn

router = APIRouter(prefix="/sessions", tags=["Sessions"])


async def _get(sid: UUID, db: AsyncSession) -> Session:
    s = (await db.execute(select(Session).where(Session.id == sid))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Session not found"})
    return s


def _s_dict(s: Session) -> dict:
    return {
        "id": str(s.id), "name": s.name, "type": s.type,
        "session_date": s.session_date.isoformat(),
        "start_time": str(s.start_time), "end_time": str(s.end_time),
        "enrollment_cap": s.enrollment_cap, "revenue_kes": float(s.revenue_kes),
        "status": s.status.value, "coach_id": str(s.coach_id),
        "venue_id": str(s.venue_id) if s.venue_id else None,
        "created_at": s.created_at.isoformat(),
    }


@router.get("", summary="List sessions")
async def list_sessions(
    pg: Pagination = Depends(),
    coach_id: UUID | None = None,
    status: str | None = None,
    from_: str = Query(None, alias="from"),
    to: str | None = None,
    db: AsyncSession = Depends(get_db)
    # ,
    # _=Depends(get_current_active_user),
):
    q = select(Session)
    if coach_id:
        q = q.where(Session.coach_id == coach_id)
    if status:
        q = q.where(Session.status == status)
    if from_:
        q = q.where(Session.session_date >= from_)
    if to:
        q = q.where(Session.session_date <= to)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.order_by(Session.session_date.desc()).offset(pg.offset).limit(pg.per_page))).scalars().all()
    return paginated([_s_dict(s) for s in rows], total, pg.page, pg.per_page)


@router.post("", status_code=201, summary="Create a session")
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)
                        #  , _=Depends(AdminOrCoach)
                         ):
    s = Session(**body.model_dump())
    db.add(s)
    await db.flush()
    await db.refresh(s)
    return ok(_s_dict(s))


@router.get("/{session_id}", summary="Get session details")
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)
                    #   , _=Depends(get_current_active_user)
                      ):
    return ok(_s_dict(await _get(session_id, db)))


@router.patch("/{session_id}", summary="Update session")
async def update_session(
    session_id: UUID, body: SessionUpdate,
    db: AsyncSession = Depends(get_db)
    # , _=Depends(AdminOrCoach),
):
    s = await _get(session_id, db)
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(s, f, v)
    await db.flush()
    return ok(_s_dict(s))


@router.delete("/{session_id}", status_code=204, summary="Cancel / delete session")
async def delete_session(session_id: UUID, db: AsyncSession = Depends(get_db)
                        #  , _=Depends(AdminOrCoach)
                         ):
    s = await _get(session_id, db)
    s.status = "cancelled"
    await db.flush()


@router.post("/{session_id}/enroll", status_code=201, summary="Enroll player in session")
async def enroll_player(
    session_id: UUID, body: EnrollIn,
    db: AsyncSession = Depends(get_db)
    # , _=Depends(get_current_active_user),
):
    s = await _get(session_id, db)
    existing = (await db.execute(
        select(SessionEnrollment).where(
            SessionEnrollment.session_id == session_id,
            SessionEnrollment.player_id == body.player_id,
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(409, {"code": "ALREADY_ENROLLED", "message": "Player already enrolled"})

    enrollment_count = (await db.execute(
        select(func.count()).where(SessionEnrollment.session_id == session_id)
    )).scalar_one()
    if enrollment_count >= s.enrollment_cap:
        raise HTTPException(422, {"code": "SESSION_FULL", "message": "Session is at capacity"})

    e = SessionEnrollment(
        session_id=session_id,
        player_id=body.player_id,
        billing_method=body.billing_method,
        player_eligibility=body.player_eligibility,
    )
    db.add(e)
    await db.flush()
    return ok({"enrollment_id": str(e.id), "session_id": str(session_id),
               "player_id": str(body.player_id), "status": e.status.value})


@router.get("/{session_id}/roster", summary="Session enrollment roster")
async def roster(session_id: UUID, db: AsyncSession = Depends(get_db)
                #  , _=Depends(get_current_active_user)
                 ):
    await _get(session_id, db)
    rows = (await db.execute(
        select(SessionEnrollment).where(SessionEnrollment.session_id == session_id)
    )).scalars().all()
    return ok([{
        "enrollment_id": str(e.id), "player_id": str(e.player_id),
        "billing_method": e.billing_method.value, "status": e.status.value,
        "enrolled_at": e.enrolled_at.isoformat(),
    } for e in rows])


@router.post("/{session_id}/checkin", summary="Pitch-side player check-in")
async def checkin(
    session_id: UUID, body: CheckInIn,
    db: AsyncSession = Depends(get_db)
    # , _=Depends(AdminOrCoach),
):
    await _get(session_id, db)
    q = select(SessionEnrollment).where(SessionEnrollment.session_id == session_id)
    if body.player_id:
        q = q.where(SessionEnrollment.player_id == body.player_id)
    enrollment = (await db.execute(q)).scalar_one_or_none()
    if not enrollment:
        raise HTTPException(404, {"code": "NOT_ENROLLED", "message": "Player not enrolled in this session"})
    enrollment.status = EnrollStatus.attended
    await db.flush()
    return ok({"player_id": str(enrollment.player_id), "status": "attended",
               "billing_triggered": enrollment.billing_method.value == "pay_as_you_go"})


@router.get("/{session_id}/revenue", summary="Session 60/40 revenue split")
async def session_revenue(session_id: UUID, db: AsyncSession = Depends(get_db)
                        #   , _=Depends(AdminOrCoach)
                          ):
    s = await _get(session_id, db)
    await db.refresh(s, ["revenue_split"])
    if s.revenue_split:
        rs = s.revenue_split
        data = {
            "session_id": str(session_id),
            "session_rate_kes": float(rs.session_rate_kes),
            "coach_pct": float(rs.coach_pct),
            "academy_pct": float(rs.academy_pct),
            "coach_amount_kes": float(rs.coach_amount_kes),
            "academy_amount_kes": float(rs.academy_amount_kes),
            "payout_status": rs.payout_status.value,
        }
    else:
        gross = float(s.revenue_kes)
        data = {
            "session_id": str(session_id),
            "session_rate_kes": gross,
            "coach_pct": 60.0,
            "academy_pct": 40.0,
            "coach_amount_kes": round(gross * 0.6, 2),
            "academy_amount_kes": round(gross * 0.4, 2),
            "payout_status": "pending",
        }
    return ok(data)
