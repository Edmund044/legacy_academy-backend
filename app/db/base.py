from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import every model so Alembic autogenerate can discover them
# from app.models.user import User  # noqa: F401,E402
from app.models.people import Campus, Coach, AcademyGroup, Player, Guardian  # noqa: F401,E402
from app.models.session import (  # noqa: F401,E402
    Venue, Session, SessionEnrollment,
    Drill, SessionPlan, SessionPlanDrill, SessionStaff,
)
from app.models.tournament import Tournament, TournamentTeam, Match  # noqa: F401,E402
from app.models.equipment import (  # noqa: F401,E402
    EquipmentItem, EquipmentHandover, HandoverItem, CoachLiability,
)
from app.models.merchandise import Product, Order, OrderItem  # noqa: F401,E402
from app.models.billing import (  # noqa: F401,E402
    Subscription, AttendanceBilling, Invoice, RevenueSplit, Payment,
)
from app.models.player_dev import (  # noqa: F401,E402
    PlayerStat, PlayerPhysical, PlayerInjury, DevTimeline, VideoHighlight,
)
from app.models.social import (  # noqa: F401,E402
    Disbursement, SponsorshipCase, CaseCost, CaseReceipt, CaseNote, SchoolFeePayment,
)
from app.models.partnership import (  # noqa: F401,E402
    SchoolPartner, Contract, RevSplitContract, ContractAudit, CoachAllocation,
)
