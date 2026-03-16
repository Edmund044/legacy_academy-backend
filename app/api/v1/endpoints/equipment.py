"""Equipment: inventory CRUD, handovers list/create, handovers return."""
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_active_user, AdminOrCoach, AdminOnly, Pagination
from app.core.responses import ok, paginated
from app.models.equipment import EquipmentItem, EquipmentHandover, HandoverItem, HandoverStatus
from app.schemas.schemas import EquipCreate, EquipUpdate, HandoverCreate, HandoverReturnIn

router = APIRouter(prefix="/equipment", tags=["Equipment"])


@router.get("/inventory", summary="List equipment inventory")
async def list_inventory(
    pg: Pagination = Depends(),
    category: str | None = None,
    campus_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    q = select(EquipmentItem)
    if category:
        q = q.where(EquipmentItem.category == category)
    if campus_id:
        q = q.where(EquipmentItem.campus_id == campus_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    data = [{
        "id": str(e.id), "name": e.name, "category": e.category.value, "sku": e.sku,
        "stock_total": e.stock_total, "stock_assigned": e.stock_assigned,
        "utilization_pct": e.utilization_pct, "condition": e.condition.value,
        "replacement_cost_usd": float(e.replacement_cost_usd) if e.replacement_cost_usd else None,
    } for e in rows]
    return paginated(data, total, pg.page, pg.per_page)


@router.post("/inventory", status_code=201, summary="Add equipment item")
async def create_equipment(body: EquipCreate, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
    e = EquipmentItem(**body.model_dump())
    db.add(e)
    await db.flush()
    return ok({"id": str(e.id), "name": e.name, "category": e.category.value})


@router.patch("/inventory/{item_id}", summary="Update equipment item")
async def update_equipment(
    item_id: UUID, body: EquipUpdate,
    db: AsyncSession = Depends(get_db), _=Depends(AdminOnly),
):
    e = (await db.execute(select(EquipmentItem).where(EquipmentItem.id == item_id))).scalar_one_or_none()
    if not e:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Equipment item not found"})
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(e, f, v)
    await db.flush()
    return ok({"id": str(e.id), "condition": e.condition.value})


@router.delete("/inventory/{item_id}", status_code=204, summary="Delete equipment item")
async def delete_equipment(item_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
    e = (await db.execute(select(EquipmentItem).where(EquipmentItem.id == item_id))).scalar_one_or_none()
    if not e:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Equipment item not found"})
    await db.delete(e)


@router.get("/handovers", summary="List equipment handovers")
async def list_handovers(
    pg: Pagination = Depends(),
    coach_id: UUID | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    q = select(EquipmentHandover)
    if coach_id:
        q = q.where(EquipmentHandover.coach_id == coach_id)
    if status:
        q = q.where(EquipmentHandover.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.order_by(EquipmentHandover.checked_out_at.desc()).offset(pg.offset).limit(pg.per_page))).scalars().all()
    data = [{
        "id": str(h.id), "coach_id": str(h.coach_id),
        "session_id": str(h.session_id) if h.session_id else None,
        "status": h.status.value,
        "checked_out_at": h.checked_out_at.isoformat(),
        "returned_at": h.returned_at.isoformat() if h.returned_at else None,
    } for h in rows]
    return paginated(data, total, pg.page, pg.per_page)


@router.post("/handovers", status_code=201, summary="Create equipment handover (check-out)")
async def create_handover(body: HandoverCreate, db: AsyncSession = Depends(get_db), _=Depends(AdminOrCoach)):
    handover = EquipmentHandover(coach_id=body.coach_id, session_id=body.session_id)
    db.add(handover)
    await db.flush()

    for item_in in body.items:
        equip = (await db.execute(select(EquipmentItem).where(EquipmentItem.id == item_in.equipment_id))).scalar_one_or_none()
        if not equip:
            raise HTTPException(404, {"code": "EQUIP_NOT_FOUND", "message": f"Equipment {item_in.equipment_id} not found"})
        if equip.stock_total - equip.stock_assigned < item_in.qty:
            raise HTTPException(422, {"code": "INSUFFICIENT_STOCK", "message": f"Not enough stock for {equip.name}"})
        equip.stock_assigned += item_in.qty
        hi = HandoverItem(
            handover_id=handover.id,
            equipment_id=item_in.equipment_id,
            qty=item_in.qty,
            condition_out=item_in.condition_out,
        )
        db.add(hi)

    await db.flush()
    return ok({"handover_id": str(handover.id), "status": handover.status.value, "items": len(body.items)})


@router.post("/handovers/{handover_id}/return", summary="Return equipment (check-in)")
async def return_handover(
    handover_id: UUID, body: HandoverReturnIn,
    db: AsyncSession = Depends(get_db), _=Depends(AdminOrCoach),
):
    h = (await db.execute(select(EquipmentHandover).where(EquipmentHandover.id == handover_id))).scalar_one_or_none()
    if not h:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Handover not found"})
    if h.status == HandoverStatus.returned:
        raise HTTPException(409, {"code": "ALREADY_RETURNED", "message": "Equipment already returned"})

    h.returned_at = datetime.now(timezone.utc)
    h.status = HandoverStatus.returned
    h.damage_notes = body.damage_notes

    for ret in body.items:
        hi = (await db.execute(
            select(HandoverItem).where(HandoverItem.id == ret.handover_item_id)
        )).scalar_one_or_none()
        if hi:
            hi.condition_in = ret.condition_in
            hi.is_lost = ret.is_lost
            hi.is_damaged = ret.is_damaged
            if not ret.is_lost:
                equip = (await db.execute(select(EquipmentItem).where(EquipmentItem.id == hi.equipment_id))).scalar_one_or_none()
                if equip:
                    equip.stock_assigned = max(0, equip.stock_assigned - hi.qty)

    await db.flush()
    return ok({"handover_id": str(handover_id), "status": "returned",
               "returned_at": h.returned_at.isoformat(), "damage_reported": bool(body.damage_notes)})
