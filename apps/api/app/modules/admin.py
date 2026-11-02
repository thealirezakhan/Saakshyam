from fastapi import APIRouter, Depends, HTTPException, Request

from ..core.config import settings
from ..core.security import AuthContext, get_auth

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/reset-demo")
def reset_demo(request: Request, auth: AuthContext = Depends(get_auth)):
    if not any(m.role == "admin" for m in auth.memberships.values()):
        raise HTTPException(403, "Admin role required")
    mode = getattr(request.app.state, "seed_mode", settings.DEMO_MODE)
    if mode not in ("aarohan", "northstar"):
        raise HTTPException(403, "Demo reset is disabled")

    request.app.state.db.reset()
    from ..seed import seed_demo_if_empty, seed_if_empty
    session = request.app.state.db.session()
    try:
        if mode == "aarohan":
            seed_demo_if_empty(session)
        else:
            seed_if_empty(session)
        session.commit()
    finally:
        session.close()
    return {"data": {"reset": True, "mode": mode,
                     "note": "Sign in again; all demo state was recreated."}}
