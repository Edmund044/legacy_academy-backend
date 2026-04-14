"""
AcademyPro API — main application entry point.
FastAPI 0.111  |  Python 3.12  |  PostgreSQL via asyncpg + SQLAlchemy 2.0
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Database setup on startup; connection pool teardown on shutdown."""
    if settings.ENVIRONMENT == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "## AcademyPro REST API\n\n"
        "Comprehensive management platform for **Legacy Football Academy**.\n\n"
        "### Domains\n"
        "- **Auth** — JWT login, refresh, password reset\n"
        "- **Users** — platform accounts, role management\n"
        "- **Coaches** — profiles, schedules, revenue\n"
        "- **Players** — profiles, stats, physical, injuries, development timeline\n"
        "- **Sessions** — lifecycle, enrollment, check-in, plans, 60/40 revenue splits\n"
        "- **Billing** — subscriptions, M-Pesa payments, invoices, attendance billing\n"
        "- **Equipment** — inventory, handovers, coach liabilities\n"
        "- **Merchandise** — products catalog, orders\n"
        "- **Social Impact** — disbursements, sponsorship cases, school fees\n"
        "- **Partnerships** — school partners, contracts, revenue restructuring\n"
        "- **Tournaments** — brackets, fixtures, live scores\n"
        "- **Analytics** — KPIs, revenue series, enrollment, social impact\n"
        "- **Auth** — Register, login, JWT-secured endpoints\n"
        "- **Accounts** — Create savings/current/loan accounts\n"
        "- **Top Up** — Credit accounts (M-Pesa, bank-in)\n"
        "- **Withdrawals** — Cash out from your account\n"
        "- **Transfers** — Send money between accounts (0.5% fee, max KES 300)\n"
        "- **Loans** — Apply → Approve → Disburse → Repay lifecycle\n"
        "- **Statement** — Paginated transaction history with category filters\n"

### Transaction Categories

#`top_up` · `deposit` · `withdrawal` · `transfer_in` · `transfer_out` · `loan_disbursement` · `loan_repayment` · `fee` · `interest`
   
    ),
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
    contact={"name": "AcademyPro Engineering", "email": "api@academypro.io"},
)


# ── Swagger Bearer auth ────────────────────────────────────────────────────────

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste the **access_token** from `POST /auth/login`. No 'Bearer' prefix needed.",
        }
    }
    # Apply BearerAuth globally to every endpoint
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi


# ── Middleware ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    # allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)


# ── Exception handlers ─────────────────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    details = [
        {
            "field": ".".join(str(l) for l in e["loc"] if l != "body"),
            "msg": e["msg"],
            "type": e["type"],
        }
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request body validation failed",
                "details": details,
            },
        },
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"success": False, "error": {"code": "NOT_FOUND", "message": "Resource not found"}},
    )


# ── Routers ────────────────────────────────────────────────────────────────────

app.include_router(api_router, prefix=settings.API_V1_STR)


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "1.0.0", "service": "academypro-api"}


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "AcademyPro API",
        "version": "1.0.0",
        "docs": f"{settings.API_V1_STR}/docs",
    }



# """
# AcademyPro API — main application entry point.
# FastAPI 0.111  |  Python 3.12  |  PostgreSQL via asyncpg + SQLAlchemy 2.0
# """
# from contextlib import asynccontextmanager

# from fastapi import FastAPI, Request, status
# from fastapi.exceptions import RequestValidationError
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.middleware.trustedhost import TrustedHostMiddleware
# from fastapi.responses import JSONResponse

# from app.api.v1.router import api_router
# from app.core.config import settings
# from app.db.session import engine
# from app.db.base import Base


# # ── Lifespan ──────────────────────────────────────────────────────────────────

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Database setup on startup; connection pool teardown on shutdown."""
#     if settings.ENVIRONMENT == "development":
#         async with engine.begin() as conn:
#             await conn.run_sync(Base.metadata.create_all)
#     yield
#     await engine.dispose()


# # ── App factory ───────────────────────────────────────────────────────────────

# app = FastAPI(
#     title=settings.PROJECT_NAME,
#     description=(
#         "## AcademyPro REST API\n\n"
#         "Comprehensive management platform for **Legacy Football Academy**.\n\n"
#         "### Domains\n"
#         "- **Auth** — JWT login, refresh, password reset\n"
#         "- **Users** — platform accounts, role management\n"
#         "- **Coaches** — profiles, schedules, revenue\n"
#         "- **Players** — profiles, stats, physical, injuries, development timeline\n"
#         "- **Sessions** — lifecycle, enrollment, check-in, plans, 60/40 revenue splits\n"
#         "- **Billing** — subscriptions, M-Pesa payments, invoices, attendance billing\n"
#         "- **Equipment** — inventory, handovers, coach liabilities\n"
#         "- **Merchandise** — products catalog, orders\n"
#         "- **Social Impact** — disbursements, sponsorship cases, school fees\n"
#         "- **Partnerships** — school partners, contracts, revenue restructuring\n"
#         "- **Tournaments** — brackets, fixtures, live scores\n"
#         "- **Analytics** — KPIs, revenue series, enrollment, social impact\n"
#     ),
#     version="1.0.0",
#     openapi_url=f"{settings.API_V1_STR}/openapi.json",
#     docs_url=f"{settings.API_V1_STR}/docs",
#     redoc_url=f"{settings.API_V1_STR}/redoc",
#     lifespan=lifespan,
#     contact={"name": "AcademyPro Engineering", "email": "api@academypro.io"},
# )


# # ── Middleware ─────────────────────────────────────────────────────────────────

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.BACKEND_CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# if settings.ENVIRONMENT == "production":
#     app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)


# # ── Exception handlers ─────────────────────────────────────────────────────────

# @app.exception_handler(RequestValidationError)
# async def validation_handler(request: Request, exc: RequestValidationError):
#     details = [
#         {
#             "field": ".".join(str(l) for l in e["loc"] if l != "body"),
#             "msg": e["msg"],
#             "type": e["type"],
#         }
#         for e in exc.errors()
#     ]
#     return JSONResponse(
#         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#         content={
#             "success": False,
#             "error": {
#                 "code": "VALIDATION_ERROR",
#                 "message": "Request body validation failed",
#                 "details": details,
#             },
#         },
#     )


# @app.exception_handler(404)
# async def not_found_handler(request: Request, exc):
#     return JSONResponse(
#         status_code=404,
#         content={"success": False, "error": {"code": "NOT_FOUND", "message": "Resource not found"}},
#     )


# # ── Routers ────────────────────────────────────────────────────────────────────

# app.include_router(api_router, prefix=settings.API_V1_STR)


# # ── Health ─────────────────────────────────────────────────────────────────────

# @app.get("/health", tags=["Health"])
# async def health():
#     return {"status": "ok", "version": "1.0.0", "service": "academypro-api"}


# @app.get("/", tags=["Health"])
# async def root():
#     return {
#         "service": "AcademyPro API",
#         "version": "1.0.0",
#         "docs": f"{settings.API_V1_STR}/docs",
#     }
