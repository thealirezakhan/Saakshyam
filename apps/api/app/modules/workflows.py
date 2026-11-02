from fastapi import APIRouter, Depends, HTTPException

from ..core.security import AuthContext, get_auth
from ..workflows import STAGES, category_catalog, get_workflow

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


@router.get("")
def list_workflows(auth: AuthContext = Depends(get_auth)):
    return {"data": category_catalog()}


@router.get("/{key}")
def workflow_detail(key: str, auth: AuthContext = Depends(get_auth)):
    try:
        w = get_workflow(key)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return {"data": {
        "key": w.key, "title": w.title, "purpose": w.purpose,
        "documents": list(w.documents), "historical_records": list(w.historical_records),
        "rule_ids": list(w.rule_ids), "outputs": list(w.outputs),
        "deficiency_types": list(w.deficiency_types),
        "evc": w.evc, "needs_confirmation": w.needs_confirmation,
        "stages": [{"key": s, "title": STAGES.get(s, s)} for s in w.stages],
    }}
