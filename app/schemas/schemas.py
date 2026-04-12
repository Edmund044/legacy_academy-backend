"""
All Pydantic v2 request/response schemas for AcademyPro API.
"""
from datetime import datetime, date, time
from typing import List, Optional
from uuid import UUID
from app.models.banking import TransactionCategory, TransactionType, LoanStatus
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ── Base config ────────────────────────────────────────────────────────────────

class Orm(BaseModel):
    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════════════════

class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = 86400
    token_type: str = "Bearer"
    user: dict


class RefreshIn(BaseModel):
    refresh_token: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    password: str = Field(min_length=8)
    password_confirm: str

    @field_validator("password_confirm")
    @classmethod
    def must_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


# ══════════════════════════════════════════════════════════════════════════════
#  USERS
# ══════════════════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: str
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: Optional[str] = None

    @field_validator("password")
    @classmethod
    def strong(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Need at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Need at least one digit")
        return v


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(Orm):
    id: UUID
    email: EmailStr
    role: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class UserSummary(Orm):
    id: UUID
    email: EmailStr
    role: str
    first_name: str
    last_name: str


# ══════════════════════════════════════════════════════════════════════════════
#  COACHES
# ══════════════════════════════════════════════════════════════════════════════

class CoachCreate(BaseModel):
    full_name: str
    license: str = Field(min_length=2, max_length=100)
    bio: Optional[str] = None
    primary_assigned_teams: Optional[List[str]] = None
    career_win_rate: Optional[int] = Field(default=None, ge=0)
    experience_years: int = Field(ge=0, le=60, default=0)
    speciality: Optional[str] = None


class CoachUpdate(BaseModel):
    license: Optional[str] = None
    bio: Optional[str] = None
    speciality: Optional[str] = None
    experience_years: Optional[int] = Field(default=None, ge=0, le=60)


class CoachOut(Orm):
    id: UUID
    user: UserSummary
    license: str
    bio: Optional[str] = None
    experience_years: int
    rating: Optional[float] = None
    speciality: Optional[str] = None
    created_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
#  PLAYERS
# ══════════════════════════════════════════════════════════════════════════════

class PlayerCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    training_center: Optional[str] = None
    group: Optional[str] = None
    height: Optional[float] = Field(default=None, gt=0, lt=300)
    weight: Optional[float] = Field(default=None, gt=0, lt=300)
    top_speed: Optional[float] = Field(default=None, gt=0, lt=60)
    bmi: Optional[float] = Field(default=None, gt=0, lt=100)
    goals: Optional[int] = None
    assists: Optional[int] = None
    pass_accuracy: Optional[float] = Field(default=None, ge=0, le=100)
    sponsored: int = False
    guardian: Optional[str] = None
    dob: date
    position: Optional[str] = None
    group_id: Optional[UUID] = None
    campus_id: Optional[UUID] = None



class PlayerUpdate(BaseModel):
    position: Optional[str] = None
    group_id: Optional[UUID] = None
    status: Optional[str] = None


class PlayerOut(Orm):
    id: UUID
    first_name: str
    last_name: str
    dob: date
    position: Optional[str] = None
    status: str
    created_at: datetime


class PlayerPhysicalCreate(BaseModel):
    assessed_at: date
    height_cm: Optional[float] = Field(default=None, gt=0, lt=300)
    weight_kg: Optional[float] = Field(default=None, gt=0, lt=300)
    top_speed: Optional[float] = Field(default=None, gt=0, lt=60)


class PlayerPhysicalOut(Orm):
    id: UUID
    assessed_at: date
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    top_speed: Optional[float] = None
    bmi: Optional[float] = None


# ══════════════════════════════════════════════════════════════════════════════
#  SESSIONS
# ══════════════════════════════════════════════════════════════════════════════

class SessionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str
    coach_id: UUID
    venue_id: Optional[UUID] = None
    session_date: date
    start_time: time   # "HH:MM"
    end_time: time
    enrollment_cap: int = Field(ge=1, le=200, default=30)
    equipment_needed: Optional[List[str]] = None
    drills: Optional[List[str]] = None  # [{"drill_id": UUID, "order": int}]


class SessionUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str
    coach_id: UUID
    venue_id: Optional[UUID] = None
    session_date: date
    start_time: time   # "HH:MM"
    end_time: time
    enrollment_cap: int = Field(ge=1, le=200, default=30)


class SessionOut(Orm):
    id: UUID
    name: str
    type: str
    session_date: date
    start_time: time
    end_time: time
    enrollment_cap: int
    revenue_kes: float
    status: str
    created_at: datetime


class EnrollIn(BaseModel):
    player_id: UUID
    billing_method: str
    player_eligibility: Optional[str] = None


class CheckInIn(BaseModel):
    player_id: UUID = None
    status: str = None


class DrillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str
    duration_min: int = Field(ge=1, le=180, default=15)
    intensity: str = "medium"
    description: Optional[str] = None


class DrillOut(Orm):
    id: UUID
    name: str
    category: str
    duration_min: int
    intensity: str
    description: Optional[str] = None
    is_custom: bool


class SessionPlanUpsert(BaseModel):
    objectives: Optional[str] = None
    goals: Optional[str] = None
    drills: List[dict] = []


# ══════════════════════════════════════════════════════════════════════════════
#  TOURNAMENTS
# ══════════════════════════════════════════════════════════════════════════════

class TournamentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    age_group: str
    format: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


class TournamentUpdate(BaseModel):
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class TournamentOut(Orm):
    id: UUID
    name: str
    age_group: str
    format: str
    status: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: datetime


class TeamCreate(BaseModel):
    team_name: str = Field(min_length=1, max_length=150)
    group_id: Optional[UUID] = None
    is_opponent: bool = False


class MatchCreate(BaseModel):
    home_team_id: UUID
    away_team_id: UUID
    venue_id: Optional[UUID] = None
    scheduled_at: datetime


class MatchScoreUpdate(BaseModel):
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    status: Optional[str] = None


class MatchOut(Orm):
    id: UUID
    tournament_id: UUID
    scheduled_at: datetime
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: str


# ══════════════════════════════════════════════════════════════════════════════
#  EQUIPMENT
# ══════════════════════════════════════════════════════════════════════════════

class EquipCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str
    sku: Optional[str] = None
    stock_total: int = Field(ge=0, default=0)
    condition: str
    replacement_cost_usd: Optional[float] = None
    campus_id: Optional[UUID] = None


class EquipUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str
    sku: Optional[str] = None
    stock_total: int = Field(ge=0, default=0)
    condition: str
    replacement_cost_usd: Optional[float] = None
    campus_id: Optional[UUID] = None


class EquipOut(Orm):
    id: UUID
    name: str
    category: str
    sku: Optional[str] = None
    stock_total: int
    stock_assigned: int
    utilization_pct: float
    condition: str


class HandoverItemIn(BaseModel):
    equipment_id: UUID
    qty: int = Field(ge=1)
    condition_out: str


class HandoverCreate(BaseModel):
    coach_id: UUID
    session_id: Optional[UUID] = None
    items: List[HandoverItemIn]


class ReturnItemIn(BaseModel):
    handover_item_id: UUID
    condition_in: str
    is_lost: bool = False
    is_damaged: bool = False


class HandoverReturnIn(BaseModel):
    items: List[ReturnItemIn]
    damage_notes: Optional[str] = None


class HandoverOut(Orm):
    id: UUID
    coach_id: UUID
    session_id: Optional[UUID] = None
    checked_out_at: datetime
    returned_at: Optional[datetime] = None
    status: str


# ══════════════════════════════════════════════════════════════════════════════
#  MERCHANDISE
# ══════════════════════════════════════════════════════════════════════════════

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    category: str
    price_kes: float = Field(gt=0)
    stock: int = Field(ge=0, default=0)
    tag: Optional[str] = None
    image_url: Optional[str] = None


class ProductUpdate(BaseModel):
    price_kes: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    tag: Optional[str] = None


class ProductOut(Orm):
    id: UUID
    name: str
    description: Optional[str] = None
    category: str
    price_kes: float
    stock: int
    tag: Optional[str] = None
    image_url: Optional[str] = None


class OrderItemIn(BaseModel):
    product_id: UUID
    qty: int = Field(ge=1)


class OrderCreate(BaseModel):
    items: List[OrderItemIn]


class OrderStatusIn(BaseModel):
    status: str


class OrderOut(Orm):
    id: UUID
    total_kes: float
    status: str
    placed_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
#  BILLING
# ══════════════════════════════════════════════════════════════════════════════

class SubCreate(BaseModel):
    player_id: UUID
    plan_type: str
    annual_fee_kes: int = Field(ge=0)
    discount_pct: float = Field(ge=0, le=100, default=0)
    scholarship_applied: bool = False
    renewal_date: Optional[date] = None


class SubUpdate(BaseModel):
    status: Optional[str] = None
    renewal_date: Optional[date] = None


class SubOut(Orm):
    id: UUID
    player_id: UUID
    plan_type: str
    annual_fee_kes: int
    discount_pct: float
    scholarship_applied: bool
    net_fee_kes: int
    status: str
    renewal_date: Optional[date] = None
    created_at: datetime


class PaymentInitiate(BaseModel):
    amount_kes: int = Field(gt=0)
    method: str
    phone: Optional[str] = None
    invoice_ids: Optional[List[UUID]] = None
    description: Optional[str] = None


class PaymentOut(Orm):
    id: UUID
    amount_kes: int
    method: str
    provider_ref: Optional[str] = None
    status: str
    paid_at: Optional[datetime] = None
    created_at: datetime


class InvoiceOut(Orm):
    id: UUID
    ref: str
    guardian_id: UUID
    period_start: date
    period_end: date
    total_kes: int
    status: str
    issued_at: Optional[datetime] = None
    created_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
#  SOCIAL IMPACT
# ══════════════════════════════════════════════════════════════════════════════

class DisbCreate(BaseModel):
    player_id: UUID
    category: str
    amount_kes: int = Field(gt=0)
    notes: Optional[str] = None


class DisbOut(Orm):
    id: UUID
    player_id: UUID
    category: str
    amount_kes: int
    notes: Optional[str] = None
    disbursed_at: datetime


class CaseCreate(BaseModel):
    player_id: UUID
    sponsor_name: str = Field(min_length=1, max_length=200)
    annual_budget_kes: int = Field(gt=0)
    start_date: date
    end_date: Optional[date] = None


class CaseUpdate(BaseModel):
    status: Optional[str] = None
    end_date: Optional[date] = None


class CaseOut(Orm):
    id: UUID
    case_ref: str
    player_id: UUID
    sponsor_name: str
    annual_budget_kes: int
    total_spent_kes: int
    remaining_kes: int
    status: str
    start_date: date
    end_date: Optional[date] = None


class CaseCostCreate(BaseModel):
    cost_date: date
    category: str
    description: str = Field(min_length=1, max_length=500)
    amount_kes: int = Field(gt=0)


class CaseNoteCreate(BaseModel):
    note_text: str = Field(min_length=1, max_length=2000)


class CaseNoteOut(Orm):
    id: UUID
    note_text: str
    created_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
#  PARTNERSHIPS
# ══════════════════════════════════════════════════════════════════════════════

class PartnerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    location: Optional[str] = None
    status: str = "prospect"


class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None


class PartnerOut(Orm):
    id: UUID
    name: str
    location: Optional[str] = None
    status: str
    created_at: datetime


class ContractCreate(BaseModel):
    school_partner_id: UUID
    contract_ref: str = Field(min_length=3, max_length=60)
    base_rate_per_student_usd: float = Field(gt=0)
    enrollment_cap: int = Field(gt=0)
    payment_cycle: str
    termination_notice_days: int = Field(ge=0, default=90)
    renewal_date: Optional[date] = None


class ContractUpdate(BaseModel):
    status: Optional[str] = None
    renewal_date: Optional[date] = None


class ContractOut(Orm):
    id: UUID
    contract_ref: str
    school_partner_id: UUID
    base_rate_per_student_usd: float
    enrollment_cap: int
    payment_cycle: str
    status: str
    renewal_date: Optional[date] = None
    created_at: datetime


class SimulateIn(BaseModel):
    school_pct: float = Field(ge=0, le=100)
    ops_pct: float = Field(ge=0, le=100)
    provider_pct: float = Field(ge=0, le=100)
    restructuring_fee_usd: Optional[float] = None

    @model_validator(mode="after")
    def pcts_sum_100(self):
        total = self.school_pct + self.ops_pct + self.provider_pct
        if abs(total - 100) > 0.01:
            raise ValueError(f"school_pct + ops_pct + provider_pct must equal 100 (got {total})")
        return self


class RestructureIn(BaseModel):
    simulation_id: UUID


class AuditOut(Orm):
    id: UUID
    event_type: str
    description: str
    created_at: datetime



# ── Transactions ──────────────────────────────────────────────────────────────

class TopUpRequest(BaseModel):
    account_id: str
    amount: float = Field(..., gt=0)
    description: Optional[str] = "Top up"


class WithdrawalRequest(BaseModel):
    account_id: str
    amount: float = Field(..., gt=0)
    description: Optional[str] = "Withdrawal"


class TransferRequest(BaseModel):
    from_account_id: str
    to_account_number: str
    amount: float = Field(..., gt=0)
    description: Optional[str] = "Transfer"


class TransactionOut(BaseModel):
    id: str
    reference: str
    transaction_type: TransactionType
    category: TransactionCategory
    amount: float
    fee: float
    balance_before: float
    balance_after: float
    description: Optional[str]
    status: str
    from_account_id: Optional[str]
    to_account_id: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Loans ─────────────────────────────────────────────────────────────────────

class LoanApplication(BaseModel):
    account_id: str
    principal: float = Field(..., gt=1000)
    duration_months: int = Field(..., ge=1, le=60)
    purpose: Optional[str] = None


class LoanApproval(BaseModel):
    interest_rate: float = Field(..., gt=0, le=100)  # annual %


class LoanRepayment(BaseModel):
    loan_id: str
    account_id: str
    amount: float = Field(..., gt=0)


class LoanOut(BaseModel):
    id: str
    account_id: str
    principal: float
    interest_rate: float
    duration_months: int
    monthly_payment: float
    total_repayable: float
    amount_repaid: float
    outstanding_balance: float
    status: LoanStatus
    purpose: Optional[str]
    disbursed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Statement ─────────────────────────────────────────────────────────────────

class StatementFilter(BaseModel):
    account_id: str
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)
    category: Optional[TransactionCategory] = None



# transactions
class GuardianCreate(BaseModel):
    first_name: str
    last_name: str
    user_id: Optional[UUID] = None
    player_id: Optional[UUID] = None
    relationship_type: str
    whatsapp_phone: Optional[str] = None
    email: Optional[str] = None
    is_primary: bool = True
    created_at: Optional[datetime] = None

class ChildCreate(BaseModel):
    parent_id: UUID
    first_name: str

class ServiceCreate(BaseModel):
    name: str
    price: float

class OrderCreate(BaseModel):
    parent_id: UUID
    items: list


class AccountCreate(BaseModel):
    account_type: str
    currency: str = "KES"
    initial_deposit: Optional[float] = 0.0
    user_id: Optional[UUID] = None