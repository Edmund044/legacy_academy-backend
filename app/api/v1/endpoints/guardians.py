"""Users: list, create, me, get, update, delete."""
from uuid import UUID
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_active_user, AdminOnly, Pagination
from app.core.responses import ok, paginated
from app.core.security import get_password_hash
from app.schemas.schemas import GuardianCreate
from app.models.people import Guardian

router = APIRouter(prefix="/guardian", tags=["Guardians"])


@router.get("", summary="List all guardian (admin)")
async def list_guardian(
    pg: Pagination = Depends(),
    db: AsyncSession = Depends(get_db),
):
    q = select(Guardian)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    data = [{
        "id": str(e.id),
        "first_name": e.first_name, 
        "last_name": e.last_name,
        "email": e.email,
        "whatsapp_phone": e.whatsapp_phone,
        "player_id": str(e.player_id),
        "relationship_type": e.relationship_type,
        "is_primary": e.is_primary,
        "created_at": e.created_at.isoformat() if e.created_at else None
    } for e in rows]
    return paginated(data, total, pg.page, pg.per_page)


@router.post("", status_code=201, summary="Create parent (admin)")
async def create_parent(
    body: GuardianCreate,
    db: AsyncSession = Depends(get_db),
):
#     {
#   "first_name": "Edmund",
#   "last_name": "Opiyo",
#   "relationship_type": "Father",
#   "whatsapp_phone": "+2470136319",
#   "email": "edmundopiyo@gmail.com",
#   "is_primary": true
# }
    # exists = (await db.execute(select(Guardian).where(User.email == body.email))).scalar_one_or_none()
    # if exists:
    #     raise HTTPException(409, {"code": "EMAIL_TAKEN", "message": "Email already registered"})

    guardian = Guardian(**body.model_dump(), referral_code=str(uuid.uuid4())[:8])
    db.add(guardian)
    await db.flush()
    return ok({"id": str(guardian.id),
        "first_name": guardian.first_name, 
        "last_name": guardian.last_name,
        "email": guardian.email,
        "whatsapp_phone": guardian.whatsapp_phone,
        "player_id": str(guardian.player_id),
        "relationship_type": guardian.relationship_type,
        "is_primary": guardian.is_primary,
        "created_at": guardian.created_at.isoformat() if guardian.created_at else None})



# @router.get("/me", summary="Get current parent profile")
# async def me(current_parent=Depends(get_current_active_parent)):
#     return ok(UserOut.model_validate(current_parent).model_dump())


# @router.get("/{parent_id}", summary="Get parent by ID")
# async def get_parent(parent_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
#     parent = (await db.execute(select(User).where(User.id == parent_id))).scalar_one_or_none()
#     if not parent:
#         raise HTTPException(404, {"code": "NOT_FOUND", "message": "User not found"})
#     return ok(UserOut.model_validate(parent).model_dump())


# @router.patch("/{parent_id}", summary="Update parent")
# async def update_parent(
#     parent_id: UUID,
#     body: UserUpdate,
#     db: AsyncSession = Depends(get_db),
#     # current_parent=Depends(get_current_active_parent),
# ):
#     # if current_parent.role.value != "admin" and current_parent.id != parent_id:
#     #     raise HTTPException(403, {"code": "FORBIDDEN", "message": "Cannot modify another parent"})
#     parent = (await db.execute(select(User).where(User.id == parent_id))).scalar_one_or_none()
#     if not parent:
#         raise HTTPException(404, {"code": "NOT_FOUND", "message": "User not found"})
#     for field, val in body.model_dump(exclude_none=True).items():
#         setattr(parent, field, val)
#     await db.flush()
#     await db.refresh(parent)
#     return ok(UserOut.model_validate(parent).model_dump())


# @router.delete("/{parent_id}", status_code=204, summary="Deactivate parent (admin)")
# async def delete_parent(parent_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
#     parent = (await db.execute(select(User).where(User.id == parent_id))).scalar_one_or_none()
#     if not parent:
#         raise HTTPException(404, {"code": "NOT_FOUND", "message": "User not found"})
#     parent.is_active = False
#     await db.flush()
