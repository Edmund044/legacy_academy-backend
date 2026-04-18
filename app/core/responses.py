from datetime import datetime, timezone
from math import ceil
from typing import Any, Optional


def ok(data: Any, meta: Optional[dict] = None) -> dict:
    r = {"success": True, "data": data, "timestamp": datetime.now(timezone.utc).isoformat()}
    if meta:
        r["meta"] = meta
    return r


def paginated(data: Any, total: int, page: int, per_page: int,meta: Optional[dict] = {}) -> dict:
    return ok(data, {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": ceil(total / per_page) if per_page else 1,
        **(meta or {})
    })



def err(code: str, message: str, details: Optional[list] = None) -> dict:
    e = {"code": code, "message": message}
    if details:
        e["details"] = details
    return {"success": False, "error": e}
