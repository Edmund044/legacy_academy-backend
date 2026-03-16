"""Session Plans: drill library CRUD + session plan upsert."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_active_user, AdminOrCoach, Pagination
from app.core.responses import ok, paginated
from app.models.session import Drill, Session, SessionPlan, SessionPlanDrill
from app.schemas.schemas import DrillCreate, SessionPlanUpsert

router = APIRouter(prefix="/session-plans", tags=["Session Plans"])


# ── Drill library ──────────────────────────────────────────────────────────────

@router.get("/drills", summary="List drill library")
async def list_drills(
    pg: Pagination = Depends(),
    category: str | None = None,
    intensity: str | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    q = select(Drill)
    if category:
        q = q.where(Drill.category == category)
    if intensity:
        q = q.where(Drill.intensity == intensity)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    return paginated([{
        "id": str(d.id), "name": d.name, "category": d.category,
        "duration_min": d.duration_min, "intensity": d.intensity.value,
        "description": d.description, "is_custom": d.is_custom,
    } for d in rows], total, pg.page, pg.per_page)


@router.post("/drills", status_code=201, summary="Add drill to library")
async def create_drill(
    body: DrillCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(AdminOrCoach),
):
    drill = Drill(**body.model_dump(), is_custom=True, created_by=current_user.id)
    db.add(drill)
    await db.flush()
    return ok({"id": str(drill.id), "name": drill.name})


@router.patch("/drills/{drill_id}", summary="Update drill")
async def update_drill(
    drill_id: UUID, body: DrillCreate,
    db: AsyncSession = Depends(get_db), _=Depends(AdminOrCoach),
):
    d = (await db.execute(select(Drill).where(Drill.id == drill_id))).scalar_one_or_none()
    if not d:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Drill not found"})
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(d, f, v)
    await db.flush()
    return ok({"id": str(d.id), "name": d.name})


@router.delete("/drills/{drill_id}", status_code=204, summary="Delete drill")
async def delete_drill(drill_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOrCoach)):
    d = (await db.execute(select(Drill).where(Drill.id == drill_id))).scalar_one_or_none()
    if not d:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Drill not found"})
    await db.delete(d)


# ── Session Plans ──────────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/plan", summary="Get session plan")
async def get_plan(session_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    plan = (await db.execute(
        select(SessionPlan).where(SessionPlan.session_id == session_id)
    )).scalar_one_or_none()
    if not plan:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "No plan for this session"})
    await db.refresh(plan, ["drills"])
    drills_data = []
    for spd in plan.drills:
        await db.refresh(spd, ["drill"])
        drills_data.append({
            "order_idx": spd.order_idx,
            "drill_id": str(spd.drill_id),
            "drill_name": spd.drill.name,
            "duration_min": spd.duration_override or spd.drill.duration_min,
            "coaching_points": spd.coaching_points,
        })
    return ok({
        "plan_id": str(plan.id), "session_id": str(session_id),
        "objectives": plan.objectives, "goals": plan.goals,
        "drills": drills_data, "updated_at": plan.updated_at.isoformat(),
    })


@router.put("/sessions/{session_id}/plan", summary="Create or update session plan")
async def upsert_plan(
    session_id: UUID, body: SessionPlanUpsert,
    db: AsyncSession = Depends(get_db), _=Depends(AdminOrCoach),
):
    # Verify session exists
    s = (await db.execute(select(Session).where(Session.id == session_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Session not found"})

    plan = (await db.execute(
        select(SessionPlan).where(SessionPlan.session_id == session_id)
    )).scalar_one_or_none()

    if plan:
        plan.objectives = body.objectives
        plan.goals = body.goals
        # Clear existing drills
        existing_drills = (await db.execute(
            select(SessionPlanDrill).where(SessionPlanDrill.session_plan_id == plan.id)
        )).scalars().all()
        for ed in existing_drills:
            await db.delete(ed)
    else:
        plan = SessionPlan(session_id=session_id, objectives=body.objectives, goals=body.goals)
        db.add(plan)
        await db.flush()

    for drill_in in body.drills:
        spd = SessionPlanDrill(
            session_plan_id=plan.id,
            drill_id=drill_in.get("drill_id"),
            order_idx=drill_in.get("order_idx", 0),
            coaching_points=drill_in.get("coaching_points"),
            duration_override=drill_in.get("duration_override"),
        )
        db.add(spd)

    await db.flush()
    return ok({"plan_id": str(plan.id), "session_id": str(session_id), "drill_count": len(body.drills)})
