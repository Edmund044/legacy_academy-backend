"""Users: list, create, me, get, update, delete."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_active_user, AdminOnly, Pagination
from app.core.responses import ok, paginated
from app.core.security import get_password_hash
from app.models.parent import User
from app.schemas.schemas import UserCreate, UserUpdate, UserOut

router = APIRouter(prefix="/parents", tags=["Users"])


@router.get("", summary="List all parents (admin)")
async def list_parents(
    pg: Pagination = Depends(),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    rows = (await db.execute(select(User).offset(pg.offset).limit(pg.per_page))).scalars().all()
    return paginated([UserOut.model_validate(u).model_dump() for u in rows], total, pg.page, pg.per_page)


@router.post("", status_code=201, summary="Create parent (admin)")
async def create_parent(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    exists = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if exists:
        raise HTTPException(409, {"code": "EMAIL_TAKEN", "message": "Email already registered"})
    parent = User(
        email=body.email,
        password_hash=get_password_hash(body.password),
        role=body.role,
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
    )
    db.add(parent)
    await db.flush()
    await db.refresh(parent)
    return ok(UserOut.model_validate(parent).model_dump())


@router.get("/me", summary="Get current parent profile")
async def me(current_parent=Depends(get_current_active_parent)):
    return ok(UserOut.model_validate(current_parent).model_dump())


@router.get("/{parent_id}", summary="Get parent by ID")
async def get_parent(parent_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
    parent = (await db.execute(select(User).where(User.id == parent_id))).scalar_one_or_none()
    if not parent:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "User not found"})
    return ok(UserOut.model_validate(parent).model_dump())


@router.patch("/{parent_id}", summary="Update parent")
async def update_parent(
    parent_id: UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    # current_parent=Depends(get_current_active_parent),
):
    # if current_parent.role.value != "admin" and current_parent.id != parent_id:
    #     raise HTTPException(403, {"code": "FORBIDDEN", "message": "Cannot modify another parent"})
    parent = (await db.execute(select(User).where(User.id == parent_id))).scalar_one_or_none()
    if not parent:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "User not found"})
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(parent, field, val)
    await db.flush()
    await db.refresh(parent)
    return ok(UserOut.model_validate(parent).model_dump())


@router.delete("/{parent_id}", status_code=204, summary="Deactivate parent (admin)")
async def delete_parent(parent_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
    parent = (await db.execute(select(User).where(User.id == parent_id))).scalar_one_or_none()
    if not parent:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "User not found"})
    parent.is_active = False
    await db.flush()
