# """Services CRUD return."""
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_active_user, AdminOrCoach, AdminOnly, Pagination
from app.core.responses import ok, paginated
from app.models.services import Service
from app.schemas.schemas import ServiceCreate

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("/", summary="List equipment services")
async def list_services(
    pg: Pagination = Depends(),
    category: str | None = None,
    campus_id: UUID | None = None,
    session_id: UUID | None = None,
    db: AsyncSession = Depends(get_db)
    # ,
    # _=Depends(get_current_active_user),
):
    q = select(Service)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    data = [{
        "id": str(e.id),
        "name": e.name, 
        "price": e.price
    } for e in rows]
    return paginated(data, total, pg.page, pg.per_page)


@router.post("/", status_code=201, summary="Add services item")
async def create_equipment(body: ServiceCreate, db: AsyncSession = Depends(get_db)
                        #    , _=Depends(AdminOnly)
                           ):
    e = Service(**body.model_dump())
    db.add(e)
    await db.flush()
    return ok({"id": str(e.id), "name": e.name, "price": e.price})


# @router.patch("/{item_id}", summary="Update equipment item")
# async def update_equipment(
#     item_id: UUID, body: EquipUpdate,
#     db: AsyncSession = Depends(get_db)
#     # , _=Depends(AdminOnly),
# ):
#     e = (await db.execute(select(EquipmentItem).where(EquipmentItem.id == item_id))).scalar_one_or_none()
#     if not e:
#         raise HTTPException(404, {"code": "NOT_FOUND", "message": "Equipment item not found"})
#     for f, v in body.model_dump(exclude_none=True).items():
#         setattr(e, f, v)
#     await db.flush()
#     return ok({"id": str(e.id), "condition": e.condition, "stock_total": e.stock_total, "stock_assigned": e.stock_assigned})


# @router.delete("/{item_id}", status_code=204, summary="Delete equipment item")
# async def delete_equipment(item_id: UUID, db: AsyncSession = Depends(get_db)
#                         #    , _=Depends(AdminOnly)
#                            ):
#     e = (await db.execute(select(EquipmentItem).where(EquipmentItem.id == item_id))).scalar_one_or_none()
#     if not e:
#         raise HTTPException(404, {"code": "NOT_FOUND", "message": "Equipment item not found"})
#     await db.delete(e)

