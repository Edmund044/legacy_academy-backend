from math import ceil
from typing import AsyncGenerator, Generator
from uuid import UUID

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal, SessionLocal
from app.models.user import User

bearer_scheme = HTTPBearer()

_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail={"code": "TOKEN_INVALID", "message": "Could not validate credentials"},
    headers={"WWW-Authenticate": "Bearer"},
)


# ── DB sessions ────────────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_db2() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Auth ───────────────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise _401
    except JWTError:
        raise _401

    user = (
        await db.execute(select(User).where(User.id == UUID(user_id)))
    ).scalar_one_or_none()

    if not user:
        raise _401
    if not user.is_active:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            {"code": "INACTIVE", "message": "Account deactivated"},
        )
    return user


async def get_current_active_user(current_user=Depends(get_current_user)):
    return current_user


# ── Role guards ────────────────────────────────────────────────────────────────

# def require_roles(*roles: str):
#     async def _check(user=Depends(get_current_active_user)):
#         # user.role may be an enum or a plain string — handle both
#         role_value = user.role.value if hasattr(user.role, "value") else user.role
#         if role_value not in roles:
#             raise HTTPException(
#                 status.HTTP_403_FORBIDDEN,
#                 {"code": "FORBIDDEN", "message": f"Requires one of: {list(roles)}"},
#             )
#         return user
#     return _check

# def require_roles(*roles: str):
#     async def _check(user=Depends(get_current_active_user)):
#         role_value = user.role.value if hasattr(user.role, "value") else user.role
#         print(f"DEBUG >>> role_value='{role_value}' | type={type(role_value)} | roles={roles}")
#         if role_value not in roles:
#             raise HTTPException(
#                 status.HTTP_403_FORBIDDEN,
#                 {"code": "FORBIDDEN", "message": f"Requires one of: {list(roles)}"},
#             )
#         return user
#     return _check
def require_roles(*roles: str):
    async def _check(user=Depends(get_current_active_user)):
        role_value = user.role.value if hasattr(user.role, "value") else user.role
        print(f">>> role_value='{role_value}' type={type(role_value)} roles={roles}")
        if role_value not in roles:
            raise HTTPException(...)
        return user
    return _check




AdminOnly        = require_roles("admin")
AdminOrCoach     = require_roles("admin", "coach")
AdminOrParent    = require_roles("admin", "parent")
CaseMgrRequired  = require_roles("admin", "case_manager")
ContractRequired = require_roles("admin", "contract_manager", "regional_admin")
AnyUser          = require_roles("admin", "coach", "parent", "case_manager",
                                 "contract_manager", "regional_admin")


# ── Pagination ─────────────────────────────────────────────────────────────────

class Pagination:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, alias="per_page"),
    ):
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page

    def meta(self, total: int) -> dict:
        return {
            "page": self.page,
            "per_page": self.per_page,
            "total": total,
            "pages": ceil(total / self.per_page) if self.per_page else 1,
        }