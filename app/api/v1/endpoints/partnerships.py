"""Partnerships: school-partners CRUD, contracts CRUD, simulate, restructure, audit."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_active_user, ContractRequired, AdminOnly, Pagination
from app.core.responses import ok, paginated
from app.models.partnership import SchoolPartner, Contract, RevSplitContract, ContractAudit, ContractStatus
from app.schemas.schemas import PartnerCreate, PartnerUpdate, ContractCreate, ContractUpdate, SimulateIn, RestructureIn

router = APIRouter(prefix="/partnerships", tags=["Partnerships"])


async def _get_partner(pid: UUID, db: AsyncSession) -> SchoolPartner:
    p = (await db.execute(select(SchoolPartner).where(SchoolPartner.id == pid))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "School partner not found"})
    return p


async def _get_contract(cid: UUID, db: AsyncSession) -> Contract:
    c = (await db.execute(select(Contract).where(Contract.id == cid))).scalar_one_or_none()
    if not c:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Contract not found"})
    return c


# ── School Partners ────────────────────────────────────────────────────────────

@router.get("/school-partners", summary="List school partners")
async def list_partners(pg: Pagination = Depends(), status: str | None = None,
                        db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    q = select(SchoolPartner)
    if status:
        q = q.where(SchoolPartner.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    return paginated([{"id": str(p.id), "name": p.name, "location": p.location,
                       "status": p.status.value, "created_at": p.created_at.isoformat()} for p in rows],
                     total, pg.page, pg.per_page)


@router.post("/school-partners", status_code=201, summary="Create school partner")
async def create_partner(body: PartnerCreate, db: AsyncSession = Depends(get_db), _=Depends(ContractRequired)):
    p = SchoolPartner(**body.model_dump())
    db.add(p)
    await db.flush()
    return ok({"id": str(p.id), "name": p.name})


@router.patch("/school-partners/{partner_id}", summary="Update school partner")
async def update_partner(partner_id: UUID, body: PartnerUpdate,
                         db: AsyncSession = Depends(get_db), _=Depends(ContractRequired)):
    p = await _get_partner(partner_id, db)
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(p, f, v)
    await db.flush()
    return ok({"id": str(p.id), "status": p.status.value})


@router.delete("/school-partners/{partner_id}", status_code=204, summary="Delete school partner")
async def delete_partner(partner_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
    p = await _get_partner(partner_id, db)
    await db.delete(p)


# ── Contracts ──────────────────────────────────────────────────────────────────

@router.get("/contracts", summary="List contracts")
async def list_contracts(pg: Pagination = Depends(), status: str | None = None,
                         db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    q = select(Contract)
    if status:
        q = q.where(Contract.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    return paginated([{
        "id": str(c.id), "contract_ref": c.contract_ref,
        "school_partner_id": str(c.school_partner_id),
        "base_rate_per_student_usd": float(c.base_rate_per_student_usd),
        "enrollment_cap": c.enrollment_cap, "payment_cycle": c.payment_cycle.value,
        "status": c.status.value, "renewal_date": c.renewal_date.isoformat() if c.renewal_date else None,
    } for c in rows], total, pg.page, pg.per_page)


@router.post("/contracts", status_code=201, summary="Create contract")
async def create_contract(body: ContractCreate, db: AsyncSession = Depends(get_db), _=Depends(ContractRequired)):
    # Validate partner exists
    await _get_partner(body.school_partner_id, db)
    c = Contract(**body.model_dump())
    db.add(c)
    await db.flush()
    audit = ContractAudit(contract_id=c.id, event_type="created", description="Contract created")
    db.add(audit)
    await db.flush()
    return ok({"id": str(c.id), "contract_ref": c.contract_ref, "status": c.status.value})


@router.patch("/contracts/{contract_id}", summary="Update contract")
async def update_contract(contract_id: UUID, body: ContractUpdate,
                          db: AsyncSession = Depends(get_db), _=Depends(ContractRequired)):
    c = await _get_contract(contract_id, db)
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(c, f, v)
    audit = ContractAudit(contract_id=c.id, event_type="updated", description=f"Fields updated: {list(body.model_dump(exclude_none=True).keys())}")
    db.add(audit)
    await db.flush()
    return ok({"id": str(c.id), "status": c.status.value})


@router.post("/contracts/{contract_id}/simulate", status_code=201, summary="Simulate revenue split restructure")
async def simulate_split(
    contract_id: UUID, body: SimulateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(ContractRequired),
):
    c = await _get_contract(contract_id, db)
    annual = float(c.base_rate_per_student_usd) * c.enrollment_cap * 12
    sim = RevSplitContract(
        contract_id=contract_id,
        school_pct=body.school_pct,
        ops_pct=body.ops_pct,
        provider_pct=body.provider_pct,
        restructuring_fee_usd=body.restructuring_fee_usd,
        is_simulation=True,
        is_active=False,
        projected_annual_usd=annual,
        created_by=current_user.id,
    )
    db.add(sim)
    await db.flush()
    return ok({
        "simulation_id": str(sim.id),
        "is_simulation": True,
        "school_pct": body.school_pct,
        "ops_pct": body.ops_pct,
        "provider_pct": body.provider_pct,
        "projected_annual_usd": annual,
        "school_share_usd": round(annual * body.school_pct / 100, 2),
        "ops_share_usd": round(annual * body.ops_pct / 100, 2),
        "provider_share_usd": round(annual * body.provider_pct / 100, 2),
        "restructuring_fee_usd": body.restructuring_fee_usd,
        "message": "Simulation saved. Call /restructure with simulation_id to apply.",
    })


@router.post("/contracts/{contract_id}/restructure", summary="Apply simulated revenue split")
async def restructure_contract(
    contract_id: UUID, body: RestructureIn,
    db: AsyncSession = Depends(get_db), current_user=Depends(ContractRequired),
):
    c = await _get_contract(contract_id, db)
    sim = (await db.execute(
        select(RevSplitContract).where(
            RevSplitContract.id == body.simulation_id,
            RevSplitContract.contract_id == contract_id,
            RevSplitContract.is_simulation == True,
        )
    )).scalar_one_or_none()
    if not sim:
        raise HTTPException(404, {"code": "SIM_NOT_FOUND", "message": "Simulation not found for this contract"})

    # Deactivate previous active splits
    prev = (await db.execute(
        select(RevSplitContract).where(
            RevSplitContract.contract_id == contract_id,
            RevSplitContract.is_active == True,
        )
    )).scalars().all()
    for p in prev:
        p.is_active = False

    sim.is_simulation = False
    sim.is_active = True

    audit = ContractAudit(
        contract_id=contract_id,
        event_type="restructured",
        description=f"Revenue split applied from simulation {sim.id}: {sim.school_pct}/{sim.ops_pct}/{sim.provider_pct}",
        author_id=current_user.id,
    )
    db.add(audit)
    await db.flush()
    return ok({"message": "Revenue split restructured and applied", "active_split_id": str(sim.id)})


@router.get("/contracts/{contract_id}/audit", summary="Contract audit trail")
async def contract_audit(contract_id: UUID, pg: Pagination = Depends(),
                         db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    await _get_contract(contract_id, db)
    q = select(ContractAudit).where(ContractAudit.contract_id == contract_id).order_by(ContractAudit.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    return paginated([{
        "id": str(a.id), "event_type": a.event_type,
        "description": a.description, "created_at": a.created_at.isoformat(),
    } for a in rows], total, pg.page, pg.per_page)
