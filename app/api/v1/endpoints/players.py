"""Players: CRUD + stats, physical, injuries, timeline, highlights."""
from pydoc import text
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, func, or_
from app.core.deps import get_db, get_current_active_user, AdminOrCoach, Pagination
from app.core.responses import ok, paginated
from app.models.people import Player, Guardian
from app.models.player_dev import PlayerStat, PlayerPhysical, PlayerInjury, DevTimeline, VideoHighlight
from app.schemas.schemas import PlayerCreate, PlayerUpdate, PlayerOut, PlayerPhysicalCreate
from app.services.whatssap_notifications import send_whatsapp_notification
from app.models.social import Disbursement, SponsorshipCase, CaseCost

router = APIRouter(prefix="/players", tags=["Players"])


async def _get(player_id: UUID, db: AsyncSession) -> Player:
    p = (await db.execute(select(Player).where(Player.id == player_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Player not found"})
    return p


def _player_dict(p: Player) -> dict:
    return {
        "id": str(p.id), "first_name": p.first_name, "last_name": p.last_name,
        "dob": p.dob.isoformat(), "position": p.position, "status": p.status.value,
        "group_id": str(p.group_id) if p.group_id else None,
        "campus_id": str(p.campus_id) if p.campus_id else None,
        "group_name": p.group if p.group else None,
        # "guardians": [
        #     {"id": g.id, "first_name": g.first_name, "last_name": g.last_name, "email": g.email, "whatsapp_phone": g.whatsapp_phone}
        #     for g in (p.guardians or [])
        # ],
        "guardian": p.guardian if p.guardian else None,
        "sponsored": p.sponsored,
        "subscriptions": [{
            "id": str(s.id),
            "player_id": str(s.player_id),
            "status": s.status,
            "start_date": s.created_at.isoformat()
        } for s in p.subscriptions],
        "training_center": p.training_center if p.training_center else None,
        "stats": {
                "goals": p.goals if p.goals else None,
                "assists": p.assists if p.assists else None,
                "pass_accuracy": float(p.pass_accuracy) if p.pass_accuracy and p.pass_accuracy else None,

        },
        "physical": {
            "height": float(p.height) if p.height else None,
            "weight": float(p.weight) if p.weight else None,
            "bmi": float(p.bmi) if p.bmi else None,
        },
        "created_at": p.created_at.isoformat(),
    }


@router.get("", summary="List players")
async def list_players(
    pg: Pagination = Depends(),
    status: str | None = None,
    group_id: UUID | None = None,
    guardian_id: UUID | None = None,
    db: AsyncSession = Depends(get_db)
    # ,
    # _=Depends(get_current_active_user),
):
    send_whatsapp_notification("254701376319", "Hello from FastAPI 🚀")
    q = select(Player).options(
        selectinload(Player.guardians),
        selectinload(Player.subscriptions),
        selectinload(Player.group))
    if status:
        q = q.where(Player.status == status)
    if group_id:
        q = q.where(Player.group_id == group_id)
    if guardian_id:
        q = q.join(Guardian, Player.guardian_id == Guardian.id)\
            .where(Guardian.user_id == guardian_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    return paginated([_player_dict(p) for p in rows], total, pg.page, pg.per_page)

@router.get("/search", summary="List players")
async def list_players(
    pg: Pagination = Depends(),
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db)
    # ,
    # _=Depends(get_current_active_user),
):
    q = select(Player).options(
        selectinload(Player.guardians),
        selectinload(Player.subscriptions),
        selectinload(Player.group))
    
    if search:
        search_term = f"%{search}%"

        q = q.where(
            # or_(
            #     Player.first_name.ilike(search_term),
            #     Player.last_name.ilike(search_term),
                Player.guardians.user_id.ilike(search)
            # )
        )
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    return paginated([_player_dict(p) for p in rows], total, pg.page, pg.per_page)


@router.post("", status_code=201, summary="Register a player")
async def create_player(body: PlayerCreate, db: AsyncSession = Depends(get_db)
                        # , _=Depends(AdminOrCoach)
                        ):
    p = Player(**body.model_dump())
    db.add(p)
    await db.flush()
    await db.refresh(p, ["subscriptions"])
    if body.sponsored == 1:
            # Create a sponsorship case for the player
            case_ref = f"SC-{str(p.id)[:8].upper()}"
            case = SponsorshipCase(player_id=p.id,
                                   case_ref=case_ref, 
                                   sponsor_name="LEGACY ACADEMY", 
                                   annual_budget_kes=70000,
                                   total_spent_kes=0,
                                   status="active",
                                   start_date=func.now(),
                                   end_date=func.now()
                                   )
            db.add(case)
            await db.flush()
        
    return ok(_player_dict(p))


@router.get("/{player_id}", summary="Get player profile")
async def get_player(player_id: UUID, db: AsyncSession = Depends(get_db)
                    #  , _=Depends(get_current_active_user)
                     ):
    return ok(_player_dict(await _get(player_id, db)))


@router.patch("/{player_id}", summary="Update player")
async def update_player(player_id: UUID, body: PlayerUpdate, db: AsyncSession = Depends(get_db)
                        # , _=Depends(AdminOrCoach)
                        ):
    p = await _get(player_id, db)
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(p, f, v)
    await db.flush()
    return ok(_player_dict(p))


@router.delete("/{player_id}", status_code=204, summary="Archive player")
async def delete_player(player_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOrCoach)):
    p = await _get(player_id, db)
    p.status = "inactive"
    await db.flush()


@router.get("/{player_id}/stats", summary="Player season stats")
async def player_stats(player_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    await _get(player_id, db)
    rows = (await db.execute(select(PlayerStat).where(PlayerStat.player_id == player_id))).scalars().all()
    return ok([{
        "id": str(r.id), "season": r.season, "goals": r.goals, "assists": r.assists,
        "matches_played": r.matches_played, "pass_accuracy": float(r.pass_accuracy) if r.pass_accuracy else None,
    } for r in rows])


@router.get("/{player_id}/physical", summary="Player physical assessment history")
async def player_physical(player_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    await _get(player_id, db)
    rows = (await db.execute(
        select(PlayerPhysical).where(PlayerPhysical.player_id == player_id).order_by(PlayerPhysical.assessed_at.desc())
    )).scalars().all()
    return ok([{
        "id": str(r.id), "assessed_at": r.assessed_at.isoformat(),
        "height_cm": float(r.height_cm) if r.height_cm else None,
        "weight_kg": float(r.weight_kg) if r.weight_kg else None,
        "top_speed": float(r.top_speed) if r.top_speed else None,
        "bmi": r.bmi,
    } for r in rows])


@router.post("/{player_id}/physical", status_code=201, summary="Log physical assessment")
async def log_physical(
    player_id: UUID,
    body: PlayerPhysicalCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(AdminOrCoach),
):
    await _get(player_id, db)
    rec = PlayerPhysical(player_id=player_id, **body.model_dump())
    db.add(rec)
    await db.flush()
    return ok({"id": str(rec.id), "assessed_at": rec.assessed_at.isoformat(), "bmi": rec.bmi})


@router.get("/{player_id}/injuries", summary="Player injury history")
async def player_injuries(player_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    await _get(player_id, db)
    rows = (await db.execute(
        select(PlayerInjury).where(PlayerInjury.player_id == player_id).order_by(PlayerInjury.occurred_at.desc())
    )).scalars().all()
    return ok([{
        "id": str(r.id), "injury_type": r.injury_type, "severity": r.severity,
        "occurred_at": r.occurred_at.isoformat(),
        "recovered_at": r.recovered_at.isoformat() if r.recovered_at else None,
        "notes": r.notes,
    } for r in rows])


@router.get("/{player_id}/timeline", summary="Player development timeline")
async def player_timeline(player_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    await _get(player_id, db)
    rows = (await db.execute(
        select(DevTimeline).where(DevTimeline.player_id == player_id).order_by(DevTimeline.event_date.desc())
    )).scalars().all()
    return ok([{
        "id": str(r.id), "event_date": r.event_date.isoformat(), "title": r.title,
        "description": r.description, "event_type": r.event_type,
    } for r in rows])


@router.get("/{player_id}/highlights", summary="Player video highlights")
async def player_highlights(player_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    await _get(player_id, db)
    rows = (await db.execute(
        select(VideoHighlight).where(VideoHighlight.player_id == player_id)
    )).scalars().all()
    return ok([{
        "id": str(r.id), "title": r.title, "url": r.url,
        "duration_sec": r.duration_sec, "description": r.description,
    } for r in rows])
