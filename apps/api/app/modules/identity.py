from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.audit import audit
from ..core.db import get_db
from ..core.security import (
    AuthContext,
    ROLE_PERMISSIONS,
    get_auth,
    issue_token,
    verify_password,
)
from ..models import AuthToken, Institution, InstitutionMembership, User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginResponse(BaseModel):
    token: str
    user_id: str
    name: str
    email: str
    institutions: list[dict]


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    memberships = db.scalars(
        select(InstitutionMembership).where(InstitutionMembership.user_id == user.id)
    ).all()
    institutions = []
    for m in memberships:
        inst = db.get(Institution, m.institution_id)
        institutions.append({
            "institution_id": str(inst.id), "name": inst.name,
            "role": m.role, "permissions": sorted(ROLE_PERMISSIONS[m.role]),
        })
    audit(db, action="auth.login", actor_id=user.id)
    token = issue_token(db, user.id)
    return LoginResponse(
        token=token, user_id=str(user.id), name=user.name, email=user.email,
        institutions=institutions,
    )


@router.post("/logout")
def logout(request: Request, auth: AuthContext = Depends(get_auth),
           db: Session = Depends(get_db)):
    header = request.headers.get("Authorization", "")
    token = header.removeprefix("Bearer ").strip()
    row = db.get(AuthToken, token)
    if row:
        db.delete(row)
    audit(db, action="auth.logout", actor_id=auth.user.id)
    db.commit()
    return {"data": {"ok": True}}


@router.get("/me")
def me(auth: AuthContext = Depends(get_auth)):
    return {"data": {
        "user_id": str(auth.user.id), "name": auth.user.name, "email": auth.user.email,
        "institutions": [
            {"institution_id": str(i), "role": m.role,
             "permissions": sorted(ROLE_PERMISSIONS[m.role])}
            for i, m in auth.memberships.items()
        ],
    }}
