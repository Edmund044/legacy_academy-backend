"""Billing endpoints: subscriptions CRUD, attendance-billing, invoices, payments, revenue-splits."""
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_,or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.deps import get_db, get_current_active_user, AdminOnly, AdminOrParent, Pagination
from app.core.responses import ok, paginated
from app.models.billing import Subscription, Invoice, Payment, RevenueSplit, PaymentStatus, PaymentMethod
from app.schemas.schemas import SubCreate, SubUpdate, PaymentInitiate, SubOut, InvoiceOut, PaymentOut
from app.models.people import Player

router = APIRouter(prefix="/billing", tags=["Billing & Payments"])


# ── Subscriptions ──────────────────────────────────────────────────────────────

@router.get("/subscriptions", summary="List subscriptions")
async def list_subs(pg: Pagination = Depends(), db: AsyncSession = Depends(get_db),
                    #  _=Depends(get_current_active_user)
                     ):
    total = (await db.execute(select(func.count()).select_from(Subscription))).scalar_one()
    total_active = (await db.execute(select(func.count()).select_from(Subscription).where(and_(Subscription.status == "active",Subscription.plan_type == "scholarship_annual",Subscription.plan_type == "annual_membership")))).scalar_one()
    net_revenue_kes = (await db.execute(select(func.sum(Subscription.net_fee_kes)).where(and_(Subscription.status == "active",Subscription.plan_type == "scholarship_annual",Subscription.plan_type == "annual_membership")))).scalar_one() or 0
    inactive_count = total - total_active
    rows = (await db.execute(select(Subscription).options(
    selectinload(Subscription.player).selectinload(Player.group)).offset(pg.offset).limit(pg.per_page))).scalars().all()
    data = [{
        "id": str(s.id),
        "player_id": str(s.player_id),
        "plan_type": s.plan_type.value,
        "annual_fee_kes": s.annual_fee_kes,
        "net_fee_kes": s.net_fee_kes,
        "scholarship_applied": s.scholarship_applied, 
        "discount_pct": s.discount_pct,
        "status": s.status.value,
        "created_at": s.created_at.isoformat(),
        "player": {
            "id": str(s.player.id),
            "first_name": s.player.first_name,
            "last_name": s.player.last_name,
            "dob": s.player.dob.isoformat(),
            "position": s.player.position,
            "status": s.player.status.value,
            "group_id": str(s.player.group_id) if s.player.group_id else None,
            "campus_id": str(s.player.campus_id) if s.player.campus_id else None,
            "group_name": s.player.group.name if s.player.group else None,
            "sponsored": s.player.sponsored,
            "training_center": s.player.training_center if s.player.training_center else None,
        },
        "renewal_date": s.renewal_date.isoformat() if s.renewal_date else None,
    } for s in rows]
    return paginated(data, total, pg.page, pg.per_page,meta={
    "total_active": total_active,
    "net_revenue_kes": net_revenue_kes,
    "inactive_count": inactive_count
})


@router.post("/subscriptions", status_code=201, summary="Create subscription")
async def create_sub(body: SubCreate, db: AsyncSession = Depends(get_db)):
    s = Subscription(**body.model_dump())
    db.add(s)
    await db.flush()
    return ok({"id": str(s.id), "plan_type": s.plan_type, "net_fee_kes": s.net_fee_kes})


@router.get("/subscriptions/{sub_id}", summary="Get subscription")
async def get_sub(sub_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    s = (await db.execute(select(Subscription).where(Subscription.id == sub_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Subscription not found"})
    return ok({"id": str(s.id), "player_id": str(s.player_id), "plan_type": s.plan_type.value,
               "annual_fee_kes": s.annual_fee_kes, "net_fee_kes": s.net_fee_kes,
               "status": s.status.value, "renewal_date": s.renewal_date.isoformat() if s.renewal_date else None})


@router.patch("/subscriptions/{sub_id}", summary="Update subscription")
async def update_sub(sub_id: UUID, body: SubUpdate, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
    s = (await db.execute(select(Subscription).where(Subscription.id == sub_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Subscription not found"})
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(s, f, v)
    await db.flush()
    return ok({"id": str(s.id), "status": s.status.value})


@router.delete("/subscriptions/{sub_id}", status_code=204, summary="Cancel subscription")
async def delete_sub(sub_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
    s = (await db.execute(select(Subscription).where(Subscription.id == sub_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Subscription not found"})
    s.status = "suspended"
    await db.flush()


# ── Attendance billing ──────────────────────────────────────────────────────────

@router.get("/attendance-billing", summary="List attendance billing records")
async def list_attendance_billing(
    pg: Pagination = Depends(),
    db: AsyncSession = Depends(get_db),
    # _=Depends(get_current_active_user),
):
    total = (await db.execute(select(func.count()).select_from(Subscription))).scalar_one()
    total_active = (await db.execute(select(func.count()).select_from(Subscription).where(and_(Subscription.status == "active",or_(Subscription.plan_type == "monthly_regular_class",Subscription.plan_type == "scholarship_regular",Subscription.plan_type == "quarterly_regular_class"))))).scalar_one()
    net_revenue_kes = (await db.execute(select(func.sum(Subscription.net_fee_kes)).where(and_(Subscription.status == "active",or_(Subscription.plan_type == "monthly_regular_class",Subscription.plan_type == "scholarship_regular",Subscription.plan_type == "quarterly_regular_class"))))).scalar_one() or 0
    inactive_count = total - total_active
    rows = (await db.execute(select(Subscription)
                             .where(and_(Subscription.status == "active",or_(Subscription.plan_type == "monthly_regular_class",Subscription.plan_type == "scholarship_regular",Subscription.plan_type == "quarterly_regular_class")))
                             .options(
    selectinload(Subscription.player).selectinload(Player.group)).offset(pg.offset).limit(pg.per_page))).scalars().all()
    data = [{
        "id": str(s.id),
        "player_id": str(s.player_id),
        "plan_type": s.plan_type.value,
        "annual_fee_kes": s.annual_fee_kes,
        "net_fee_kes": s.net_fee_kes,
        "scholarship_applied": s.scholarship_applied, 
        "discount_pct": s.discount_pct,
        "status": s.status.value,
        "created_at": s.created_at.isoformat(),
        "player": {
            "id": str(s.player.id),
            "first_name": s.player.first_name,
            "last_name": s.player.last_name,
            "dob": s.player.dob.isoformat(),
            "position": s.player.position,
            "status": s.player.status.value,
            "group_id": str(s.player.group_id) if s.player.group_id else None,
            "campus_id": str(s.player.campus_id) if s.player.campus_id else None,
            "group_name": s.player.group.name if s.player.group else None,
            "sponsored": s.player.sponsored,
            "training_center": s.player.training_center if s.player.training_center else None,
        },
        "renewal_date": s.renewal_date.isoformat() if s.renewal_date else None,
    } for s in rows]
    return paginated(data, total, pg.page, pg.per_page,meta={
    "total_active": total_active,
    "net_revenue_kes": net_revenue_kes,
    "inactive_count": inactive_count
})


# ── Invoices ───────────────────────────────────────────────────────────────────

@router.get("/invoices", summary="List invoices")
async def list_invoices(pg: Pagination = Depends(), db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    total = (await db.execute(select(func.count()).select_from(Invoice))).scalar_one()
    rows = (await db.execute(select(Invoice).offset(pg.offset).limit(pg.per_page))).scalars().all()
    data = [{"id": str(i.id), "ref": i.ref, "total_kes": i.total_kes,
             "status": i.status.value, "issued_at": i.issued_at.isoformat() if i.issued_at else None} for i in rows]
    return paginated(data, total, pg.page, pg.per_page)


@router.get("/invoices/{invoice_id}", summary="Get invoice")
async def get_invoice(invoice_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    inv = (await db.execute(select(Invoice).where(Invoice.id == invoice_id))).scalar_one_or_none()
    if not inv:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Invoice not found"})
    return ok({"id": str(inv.id), "ref": inv.ref, "total_kes": inv.total_kes, "status": inv.status.value})


@router.get("/invoices/{invoice_id}/download", summary="Download invoice PDF")
async def download_invoice(invoice_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    inv = (await db.execute(select(Invoice).where(Invoice.id == invoice_id))).scalar_one_or_none()
    if not inv:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Invoice not found"})
    # TODO: generate PDF and return FileResponse
    return ok({"invoice_id": str(invoice_id), "pdf_url": f"/v1/billing/invoices/{invoice_id}/pdf"})


# ── Payments ───────────────────────────────────────────────────────────────────

@router.post("/payments/initiate", status_code=201, summary="Initiate M-Pesa STK push or Stripe checkout")
async def initiate_payment(
    body: PaymentInitiate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    p = Payment(
        payer_id=current_user.id,
        amount_kes=body.amount_kes,
        method=body.method,
        description=body.description,
        status=PaymentStatus.pending,
    )
    db.add(p)
    await db.flush()

    if body.method == "mpesa":
        # TODO: call Daraja STK Push API
        return ok({
            "payment_id": str(p.id),
            "method": "mpesa",
            "stk_push_sent": True,
            "message": "STK push sent to phone. Approve within 60s.",
            "checkout_request_id": f"FAKE_{p.id}",
        })
    else:
        return ok({"payment_id": str(p.id), "method": body.method, "status": "pending"})


@router.get("/payments/{payment_id}/status", summary="Poll payment status")
async def payment_status(payment_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    p = (await db.execute(select(Payment).where(Payment.id == payment_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Payment not found"})
    return ok({"payment_id": str(p.id), "status": p.status.value,
               "amount_kes": p.amount_kes, "paid_at": p.paid_at.isoformat() if p.paid_at else None})


# ── Revenue splits ─────────────────────────────────────────────────────────────

@router.get("/revenue-splits", summary="List revenue splits")
async def list_splits(
    pg: Pagination = Depends(),
    coach_id: UUID | None = None,
    payout_status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    q = select(RevenueSplit)
    if coach_id:
        q = q.where(RevenueSplit.coach_id == coach_id)
    if payout_status:
        q = q.where(RevenueSplit.payout_status == payout_status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    data = [{
        "id": str(r.id), "session_id": str(r.session_id), "coach_id": str(r.coach_id),
        "session_rate_kes": float(r.session_rate_kes),
        "coach_pct": float(r.coach_pct), "academy_pct": float(r.academy_pct),
        "coach_amount_kes": float(r.coach_amount_kes),
        "academy_amount_kes": float(r.academy_amount_kes),
        "payout_status": r.payout_status.value,
    } for r in rows]
    return paginated(data, total, pg.page, pg.per_page)
