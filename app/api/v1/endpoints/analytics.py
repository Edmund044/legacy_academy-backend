"""Analytics: dashboard, revenue, attendance, enrollment, social-impact, partnerships."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_active_user, AdminOnly
from app.core.responses import ok
from app.models.session import Session, SessionEnrollment
from app.models.billing import Payment, RevenueSplit, PaymentStatus
from app.models.people import Player, Coach
from app.models.social import Disbursement, SponsorshipCase

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", summary="Dashboard KPIs")
async def dashboard(db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    """Aggregated KPIs for the admin dashboard."""
    total_players = (await db.execute(select(func.count()).select_from(Player))).scalar_one()
    total_coaches = (await db.execute(select(func.count()).select_from(Coach))).scalar_one()
    total_sessions = (await db.execute(select(func.count()).select_from(Session))).scalar_one()
    total_revenue = (await db.execute(
        select(func.coalesce(func.sum(Payment.amount_kes), 0))
        .where(Payment.status == PaymentStatus.completed)
    )).scalar_one()
    active_cases = (await db.execute(
        select(func.count()).select_from(SponsorshipCase).where(SponsorshipCase.status == "active")
    )).scalar_one()

    return ok({
        "kpis": {
            "total_players": total_players,
            "total_coaches": total_coaches,
            "total_sessions": total_sessions,
            "total_revenue_kes": int(total_revenue),
            "active_sponsorship_cases": active_cases,
        },
        "recent_sessions": [],    # TODO: last 5 sessions
        "revenue_trend": [],      # TODO: 30-day rolling
    })


@router.get("/revenue", summary="Revenue analytics")
async def revenue_analytics(
    from_: str = Query(None, alias="from"),
    to: str = Query(None),
    group_by: str = Query("month", description="day | week | month"),
    db: AsyncSession = Depends(get_db),
    _=Depends(AdminOnly),
):
    """Revenue over time with 60/40 split breakdown."""
    # TODO: aggregate RevenueSplit by period
    return ok({
        "period": {"from": from_, "to": to, "group_by": group_by},
        "total_gross_kes": 0,
        "total_coach_share_kes": 0,
        "total_academy_share_kes": 0,
        "series": [],   # [{period, gross, coach_share, academy_share}]
    })


@router.get("/attendance", summary="Attendance analytics")
async def attendance_analytics(
    from_: str = Query(None, alias="from"),
    to: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    """Attendance rates across sessions."""
    attended = (await db.execute(
        select(func.count()).select_from(SessionEnrollment).where(SessionEnrollment.status == "attended")
    )).scalar_one()
    enrolled = (await db.execute(
        select(func.count()).select_from(SessionEnrollment)
    )).scalar_one()
    rate = round(attended / enrolled * 100, 1) if enrolled else 0.0
    return ok({
        "period": {"from": from_, "to": to},
        "total_enrolled": enrolled,
        "total_attended": attended,
        "attendance_rate_pct": rate,
        "by_session_type": [],   # TODO
    })


@router.get("/enrollment", summary="Enrollment analytics")
async def enrollment_analytics(
    from_: str = Query(None, alias="from"),
    to: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    """Enrollment volume by billing method and status."""
    total = (await db.execute(select(func.count()).select_from(SessionEnrollment))).scalar_one()
    return ok({
        "period": {"from": from_, "to": to},
        "total_enrollments": total,
        "by_billing_method": {},  # TODO
        "by_status": {},
        "trend": [],
    })


@router.get("/social-impact", summary="Social impact analytics")
async def social_impact_analytics(
    from_: str = Query(None, alias="from"),
    to: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    """Disbursement breakdown and sponsorship case overview."""
    total_disbursed = (await db.execute(
        select(func.coalesce(func.sum(Disbursement.amount_kes), 0))
    )).scalar_one()
    case_counts = (await db.execute(select(func.count()).select_from(SponsorshipCase))).scalar_one()
    return ok({
        "period": {"from": from_, "to": to},
        "total_disbursed_kes": int(total_disbursed),
        "total_cases": case_counts,
        "by_category": {},   # TODO
        "utilization_pct": 0,
    })


@router.get("/partnerships", summary="Partnership analytics")
async def partnerships_analytics(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    """Active contracts, enrollment coverage, revenue pipeline."""
    return ok({
        "active_contracts": 0,
        "total_enrollment_cap": 0,
        "active_students": 0,
        "monthly_revenue_usd": 0,
        "contracts_by_status": {},
        "renewal_pipeline": [],
    })
