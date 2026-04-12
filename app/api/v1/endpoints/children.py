# """Users: list, create, me, get, update, delete."""
# from uuid import UUID
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy import select, func
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.core.deps import get_db, get_current_active_user, AdminOnly, Pagination
# from app.core.responses import ok, paginated
# from app.core.security import get_password_hash
# from app.models.children import User
# from app.schemas.schemas import UserCreate, UserUpdate, UserOut

# router = APIRouter(prefix="/childrens", tags=["Users"])


# @router.get("", summary="List all childrens (admin)")
# async def list_childrens(
#     pg: Pagination = Depends(),
#     db: AsyncSession = Depends(get_db),
# ):
#     total = (await db.execute(select(func.count()).select_from(User))).scalar_one()
#     rows = (await db.execute(select(User).offset(pg.offset).limit(pg.per_page))).scalars().all()
#     return paginated([UserOut.model_validate(u).model_dump() for u in rows], total, pg.page, pg.per_page)


# @router.post("", status_code=201, summary="Create children (admin)")
# async def create_children(
#     body: UserCreate,
#     db: AsyncSession = Depends(get_db),
# ):
#     exists = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
#     if exists:
#         raise HTTPException(409, {"code": "EMAIL_TAKEN", "message": "Email already registered"})
#     children = User(
#         email=body.email,
#         password_hash=get_password_hash(body.password),
#         role=body.role,
#         first_name=body.first_name,
#         last_name=body.last_name,
#         phone=body.phone,
#     )
#     db.add(children)
#     await db.flush()
#     await db.refresh(children)
#     return ok(UserOut.model_validate(children).model_dump())


# @router.get("/me", summary="Get current children profile")
# async def me(current_children=Depends(get_current_active_children)):
#     return ok(UserOut.model_validate(current_children).model_dump())


# @router.get("/{children_id}", summary="Get children by ID")
# async def get_children(children_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
#     children = (await db.execute(select(User).where(User.id == children_id))).scalar_one_or_none()
#     if not children:
#         raise HTTPException(404, {"code": "NOT_FOUND", "message": "User not found"})
#     return ok(UserOut.model_validate(children).model_dump())


# @router.patch("/{children_id}", summary="Update children")
# async def update_children(
#     children_id: UUID,
#     body: UserUpdate,
#     db: AsyncSession = Depends(get_db),
#     # current_children=Depends(get_current_active_children),
# ):
#     # if current_children.role.value != "admin" and current_children.id != children_id:
#     #     raise HTTPException(403, {"code": "FORBIDDEN", "message": "Cannot modify another children"})
#     children = (await db.execute(select(User).where(User.id == children_id))).scalar_one_or_none()
#     if not children:
#         raise HTTPException(404, {"code": "NOT_FOUND", "message": "User not found"})
#     for field, val in body.model_dump(exclude_none=True).items():
#         setattr(children, field, val)
#     await db.flush()
#     await db.refresh(children)
#     return ok(UserOut.model_validate(children).model_dump())


# @router.delete("/{children_id}", status_code=204, summary="Deactivate children (admin)")
# async def delete_children(children_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
#     children = (await db.execute(select(User).where(User.id == children_id))).scalar_one_or_none()
#     if not children:
#         raise HTTPException(404, {"code": "NOT_FOUND", "message": "User not found"})
#     children.is_active = False
#     await db.flush()
