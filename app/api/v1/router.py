"""
Master API router — registers all v1 endpoint modules.
115 endpoints across 15 domains.
"""
from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.coaches import router as coaches_router
from app.api.v1.endpoints.players import router as players_router
from app.api.v1.endpoints.sessions import router as sessions_router
from app.api.v1.endpoints.billing import router as billing_router
from app.api.v1.endpoints.equipment import router as equipment_router
from app.api.v1.endpoints.merchandise import router as merchandise_router
from app.api.v1.endpoints.social import router as social_router
from app.api.v1.endpoints.partnerships import router as partnerships_router
from app.api.v1.endpoints.tournaments import router as tournaments_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.session_plans import router as session_plans_router
from app.api.v1.endpoints.loans import router as loans_router
from app.api.v1.endpoints.transactions import router as transactions_router
from app.api.v1.endpoints.services import router as services_router
from app.api.v1.endpoints.accounts import router as accounts_router
from app.api.v1.endpoints.guardians import router as guardians_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(coaches_router)
api_router.include_router(players_router)
api_router.include_router(sessions_router)
api_router.include_router(session_plans_router)
api_router.include_router(billing_router)
api_router.include_router(equipment_router)
api_router.include_router(merchandise_router)
api_router.include_router(social_router)
api_router.include_router(partnerships_router)
api_router.include_router(tournaments_router)
api_router.include_router(analytics_router)
api_router.include_router(loans_router)
api_router.include_router(transactions_router)
api_router.include_router(services_router)
api_router.include_router(accounts_router)
api_router.include_router(guardians_router)
# api_router.include_router(parents.router)
# api_router.include_router(children.router)
# api_router.include_router(services.router)
# api_router.include_router(orders.router)
# api_router.include_router(payments.router)