"""Users: list, create, me, get, update, delete."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_active_user, AdminOnly, Pagination
from app.core.responses import ok, paginated
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.schemas import UserCreate, UserUpdate, UserOut

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", summary="List all users (admin)")
async def list_users(
    pg: Pagination = Depends(),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    rows = (await db.execute(select(User).offset(pg.offset).limit(pg.per_page))).scalars().all()
    return paginated([UserOut.model_validate(u).model_dump() for u in rows], total, pg.page, pg.per_page)


@router.post("", status_code=201, summary="Create user (admin)")
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    exists = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if exists:
        raise HTTPException(409, {"code": "EMAIL_TAKEN", "message": "Email already registered"})
    user = User(
        email=body.email,
        password_hash=get_password_hash(body.password),
        role=body.role,
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return ok(UserOut.model_validate(user).model_dump())


@router.get("/me", summary="Get current user profile")
async def me(current_user=Depends(get_current_active_user)):
    return ok(UserOut.model_validate(current_user).model_dump())


@router.get("/{user_id}", summary="Get user by ID")
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "User not found"})
    return ok(UserOut.model_validate(user).model_dump())


@router.patch("/{user_id}", summary="Update user")
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    # current_user=Depends(get_current_active_user),
):
    # if current_user.role.value != "admin" and current_user.id != user_id:
    #     raise HTTPException(403, {"code": "FORBIDDEN", "message": "Cannot modify another user"})
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "User not found"})
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(user, field, val)
    await db.flush()
    await db.refresh(user)
    return ok(UserOut.model_validate(user).model_dump())


@router.delete("/{user_id}", status_code=204, summary="Deactivate user (admin)")
async def delete_user(user_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "User not found"})
    user.is_active = False
    await db.flush()
