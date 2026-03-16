# AcademyPro API

> FastAPI 0.111 · Python 3.12 · PostgreSQL 16 · SQLAlchemy 2.0 (async) · Alembic · JWT auth

Comprehensive REST API for Legacy Football Academy's AcademyPro management platform.

---

## Quick Start

### 1 — Prerequisites
- Python 3.12+
- PostgreSQL 16 running locally (or Docker)

### 2 — Install & configure
```bash
git clone <repo>
cd academypro-api

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — set SECRET_KEY and DATABASE_URL at minimum
```

### 3 — Database setup
```bash
# Create the database
createdb academypro

# Run migrations (generates all tables)
alembic upgrade head
```

### 4 — Run
```bash
uvicorn main:app --reload
```

| URL | Description |
|-----|-------------|
| http://localhost:8000/v1/docs | Swagger UI (interactive) |
| http://localhost:8000/v1/redoc | ReDoc reference |
| http://localhost:8000/v1/openapi.json | OpenAPI 3.1 spec |
| http://localhost:8000/health | Health check |

---

## Docker (recommended)

```bash
cp .env.example .env          # configure as needed
docker compose up --build     # starts PostgreSQL + API
```

API available at http://localhost:8000

---

## Project Structure

```
academypro-api/
├── main.py                        # FastAPI app factory, middleware, exception handlers
├── requirements.txt
├── alembic.ini
├── alembic/
│   ├── env.py                     # Async migration runner
│   └── versions/                  # Generated migration files
├── app/
│   ├── api/v1/
│   │   ├── router.py              # Master router — wires all 13 sub-routers
│   │   └── endpoints/
│   │       ├── auth.py            # POST /auth/login|refresh|logout|forgot-password|reset-password
│   │       ├── users.py           # GET/POST /users, GET/PATCH/DELETE /users/{id}, GET /users/me
│   │       ├── coaches.py         # CRUD + /sessions, /revenue, /schedule
│   │       ├── players.py         # CRUD + /stats, /physical, /injuries, /timeline, /highlights
│   │       ├── sessions.py        # CRUD + /enroll, /roster, /checkin, /revenue
│   │       ├── session_plans.py   # Drill library CRUD + session plan upsert
│   │       ├── billing.py         # Subscriptions, invoices, payments, revenue-splits
│   │       ├── equipment.py       # Inventory CRUD + handovers + return
│   │       ├── merchandise.py     # Products CRUD + orders CRUD + status
│   │       ├── social.py          # Disbursements + sponsorship cases + costs/receipts/notes
│   │       ├── partnerships.py    # School partners + contracts + simulate/restructure + audit
│   │       ├── tournaments.py     # Tournament CRUD + teams + matches + score
│   │       └── analytics.py       # Dashboard, revenue, attendance, enrollment, social, partnerships
│   ├── core/
│   │   ├── config.py              # Pydantic-settings — all env vars
│   │   ├── security.py            # JWT create/decode, bcrypt hash/verify
│   │   ├── deps.py                # get_db, get_current_user, role guards, Pagination
│   │   └── responses.py           # ok(), paginated(), err() envelope helpers
│   ├── db/
│   │   ├── session.py             # Async engine + session factory
│   │   └── base.py                # DeclarativeBase + all model imports for Alembic
│   ├── models/                    # SQLAlchemy ORM models (40 tables)
│   │   ├── user.py
│   │   ├── people.py              # Campus, Coach, AcademyGroup, Player, Guardian
│   │   ├── session.py             # Venue, Session, SessionEnrollment, Drill, SessionPlan, SessionStaff
│   │   ├── tournament.py          # Tournament, TournamentTeam, Match
│   │   ├── equipment.py           # EquipmentItem, EquipmentHandover, HandoverItem, CoachLiability
│   │   ├── merchandise.py         # Product, Order, OrderItem
│   │   ├── billing.py             # Subscription, AttendanceBilling, Invoice, RevenueSplit, Payment
│   │   ├── player_dev.py          # PlayerStat, PlayerPhysical, PlayerInjury, DevTimeline, VideoHighlight
│   │   ├── social.py              # Disbursement, SponsorshipCase, CaseCost, CaseReceipt, CaseNote
│   │   └── partnership.py         # SchoolPartner, Contract, RevSplitContract, ContractAudit, CoachAllocation
│   └── schemas/
│       └── schemas.py             # All Pydantic v2 request/response schemas
└── tests/
    └── test_health.py
```

---

## API Overview

### Authentication

All endpoints (except `/auth/login`, `/auth/forgot-password`, `/health`) require:
```
Authorization: Bearer <access_token>
```

Login → `POST /v1/auth/login` → returns `access_token` (24h) + `refresh_token` (30d).

### Standard Response Envelope

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-03-11T08:00:00+00:00"
}
```

**Paginated:**
```json
{
  "success": true,
  "data": [...],
  "meta": { "page": 1, "per_page": 20, "total": 150, "pages": 8 },
  "timestamp": "..."
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Player not found",
    "details": []
  }
}
```

### Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access |
| `coach` | Own sessions, players, equipment |
| `parent` | Own player's data, bookings, invoices |
| `case_manager` | Social impact, sponsorship cases |
| `contract_manager` | School partnerships, contracts |
| `regional_admin` | Cross-campus read + contract management |

### Pagination

All list endpoints support:
```
?page=1&per_page=20&sort=created_at&order=desc&search=query&from=2026-01-01&to=2026-12-31
```

---

## Key Business Rules

| Rule | Enforcement |
|------|-------------|
| Revenue split 60% coach / 40% academy | `CHECK(coach_pct + academy_pct = 100)` on `revenue_splits` |
| Contract restructure: simulate first | `/simulate` creates a record with `is_simulation=True`, `/restructure` applies it |
| M-Pesa STK push | `POST /billing/payments/initiate` with `method=mpesa` and `phone` |
| Equipment stock constraint | `CHECK(stock_assigned <= stock_total)` on `equipment_items` |
| Duplicate enrollment prevented | `UNIQUE(session_id, player_id)` on `session_enrollments` |

---

## Development

### New migration after model change
```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

### Run tests
```bash
pytest tests/ -v
```

### Generate Postman collection
Import `/v1/openapi.json` directly into Postman.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | — | JWT signing key (required in production) |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL async connection string |
| `ENVIRONMENT` | `development` | Controls table auto-creation and trusted-host middleware |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Access token lifetime |
| `MPESA_CONSUMER_KEY` | — | Daraja API consumer key |
| `MPESA_PASSKEY` | — | Daraja STK push passkey |

See `.env.example` for all variables.
