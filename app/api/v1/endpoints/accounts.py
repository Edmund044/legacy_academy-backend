from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlalchemy import select,func
from app.core.deps import get_db, Pagination
from app.models.user import User
from app.schemas.schemas import AccountCreate
from app.services import banking
from app.models.banking import Account
from app.core.responses import ok, paginated

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("/", status_code=201)
async def create_account(
    payload: AccountCreate,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    return await banking.create_account(
        db=db,
        user_id=payload.user_id,
        account_type=payload.account_type,
        currency=payload.currency,
        initial_deposit=payload.initial_deposit,
    )


@router.get("/", summary="List accounts")
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    pg: Pagination = Depends(),
):
    q = select(Account)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    data = [{
        "id": str(e.id),
        "account_type": e.account_type, 
        "currency": e.currency,
        "balance": e.balance,
    } for e in rows]
    return paginated(data, total, pg.page, pg.per_page)
