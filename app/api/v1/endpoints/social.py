"""Social Impact: disbursements list/create, sponsorship cases CRUD, costs/receipts/notes."""
import uuid as uuid_lib
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_active_user, CaseMgrRequired, Pagination
from app.core.responses import ok, paginated
from app.models.social import Disbursement, SponsorshipCase, CaseCost, CaseReceipt, CaseNote
from app.schemas.schemas import DisbCreate, CaseCreate, CaseUpdate, CaseCostCreate, CaseNoteCreate

router = APIRouter(prefix="/social-impact", tags=["Social Impact"])


async def _get_case(case_id: UUID, db: AsyncSession) -> SponsorshipCase:
    c = (await db.execute(select(SponsorshipCase).where(SponsorshipCase.id == case_id))).scalar_one_or_none()
    if not c:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Sponsorship case not found"})
    return c


# ── Disbursements ──────────────────────────────────────────────────────────────

@router.get("/disbursements", summary="List disbursements")
async def list_disbursements(
    pg: Pagination = Depends(),
    player_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    q = select(Disbursement)
    if player_id:
        q = q.where(Disbursement.player_id == player_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.order_by(Disbursement.disbursed_at.desc()).offset(pg.offset).limit(pg.per_page))).scalars().all()
    data = [{"id": str(d.id), "player_id": str(d.player_id), "category": d.category.value,
             "amount_kes": d.amount_kes, "notes": d.notes, "disbursed_at": d.disbursed_at.isoformat()} for d in rows]
    return paginated(data, total, pg.page, pg.per_page)


@router.post("/disbursements", status_code=201, summary="Record disbursement")
async def create_disbursement(
    body: DisbCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(CaseMgrRequired),
):
    d = Disbursement(**body.model_dump(), disbursed_by=current_user.id)
    db.add(d)
    await db.flush()
    return ok({"id": str(d.id), "amount_kes": d.amount_kes, "category": d.category.value})


# ── Sponsorship Cases ──────────────────────────────────────────────────────────

@router.get("/sponsorship-cases", summary="List sponsorship cases")
async def list_cases(
    pg: Pagination = Depends(),
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    q = select(SponsorshipCase)
    if status:
        q = q.where(SponsorshipCase.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    data = [{"id": str(c.id), "case_ref": c.case_ref, "player_id": str(c.player_id),
             "sponsor_name": c.sponsor_name, "annual_budget_kes": c.annual_budget_kes,
             "total_spent_kes": c.total_spent_kes, "remaining_kes": c.remaining_kes,
             "status": c.status.value} for c in rows]
    return paginated(data, total, pg.page, pg.per_page)


@router.post("/sponsorship-cases", status_code=201, summary="Open sponsorship case")
async def create_case(body: CaseCreate, db: AsyncSession = Depends(get_db), _=Depends(CaseMgrRequired)):
    case_ref = f"SC-{str(uuid_lib.uuid4())[:8].upper()}"
    c = SponsorshipCase(**body.model_dump(), case_ref=case_ref)
    db.add(c)
    await db.flush()
    return ok({"id": str(c.id), "case_ref": c.case_ref})


@router.get("/sponsorship-cases/{case_id}", summary="Get case details")
async def get_case(case_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    c = await _get_case(case_id, db)
    return ok({
        "id": str(c.id), "case_ref": c.case_ref, "player_id": str(c.player_id),
        "sponsor_name": c.sponsor_name, "annual_budget_kes": c.annual_budget_kes,
        "total_spent_kes": c.total_spent_kes, "remaining_kes": c.remaining_kes,
        "status": c.status.value, "start_date": c.start_date.isoformat(),
        "end_date": c.end_date.isoformat() if c.end_date else None,
    })


@router.patch("/sponsorship-cases/{case_id}", summary="Update case status")
async def update_case(case_id: UUID, body: CaseUpdate, db: AsyncSession = Depends(get_db), _=Depends(CaseMgrRequired)):
    c = await _get_case(case_id, db)
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(c, f, v)
    await db.flush()
    return ok({"id": str(c.id), "status": c.status.value})


@router.post("/sponsorship-cases/{case_id}/costs", status_code=201, summary="Log case cost")
async def log_cost(case_id: UUID, body: CaseCostCreate, db: AsyncSession = Depends(get_db), _=Depends(CaseMgrRequired)):
    c = await _get_case(case_id, db)
    cost = CaseCost(case_id=case_id, **body.model_dump())
    db.add(cost)
    c.total_spent_kes += body.amount_kes
    await db.flush()
    return ok({"cost_id": str(cost.id), "amount_kes": cost.amount_kes, "remaining_kes": c.remaining_kes})


@router.post("/sponsorship-cases/{case_id}/receipts", status_code=201, summary="Upload receipt")
async def upload_receipt(
    case_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(CaseMgrRequired),
):
    await _get_case(case_id, db)
    # TODO: upload file to S3 and get URL
    fake_url = f"https://cdn.academypro.io/receipts/{case_id}/{file.filename}"
    receipt = CaseReceipt(case_id=case_id, filename=file.filename, file_url=fake_url)
    db.add(receipt)
    await db.flush()
    return ok({"receipt_id": str(receipt.id), "filename": file.filename, "file_url": fake_url})


@router.get("/sponsorship-cases/{case_id}/notes", summary="List case notes")
async def list_notes(case_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    await _get_case(case_id, db)
    rows = (await db.execute(
        select(CaseNote).where(CaseNote.case_id == case_id).order_by(CaseNote.created_at.desc())
    )).scalars().all()
    return ok([{"id": str(n.id), "note_text": n.note_text, "created_at": n.created_at.isoformat()} for n in rows])


@router.post("/sponsorship-cases/{case_id}/notes", status_code=201, summary="Add case note")
async def add_note(
    case_id: UUID, body: CaseNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(CaseMgrRequired),
):
    await _get_case(case_id, db)
    note = CaseNote(case_id=case_id, note_text=body.note_text, author_id=current_user.id)
    db.add(note)
    await db.flush()
    return ok({"note_id": str(note.id)})
