import hashlib
import hmac
import secrets
from datetime import timedelta

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AuthToken, InstitutionMembership, User
from .db import get_db, utcnow

TOKEN_TTL = timedelta(hours=12)

# Role -> permission map (systemdesign 5.1). ponytail: code constants, not DB tables;
# migrate to tables when custom roles exist.
ROLE_PERMISSIONS = {
    "admin": {
        "application.read", "application.draft.update", "document.upload",
        "document.read", "validation.run", "report.export", "task.create",
        "evc.manage", "review.manage",
    },
    "preparer": {
        "application.read", "application.draft.update", "document.upload",
        "document.read", "validation.run", "report.export", "task.create",
    },
    "compliance": {
        "application.read", "document.read", "validation.run",
        "report.export", "task.create", "evc.manage", "review.manage",
    },
    "reviewer": {"application.read", "document.read", "review.manage", "evc.manage"},
    "evc": {"application.read", "document.read", "report.export", "evc.manage"},
}


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, _ = stored.split("$", 1)
    return hmac.compare_digest(hash_password(password, salt), stored)


def issue_token(db: Session, user_id) -> str:
    token = secrets.token_urlsafe(32)
    db.add(AuthToken(
        token=token, user_id=user_id,
        expires_at=utcnow() + TOKEN_TTL,
    ))
    db.commit()
    return token


class AuthContext:
    def __init__(self, user: User, memberships: list[InstitutionMembership]):
        self.user = user
        self.memberships = {m.institution_id: m for m in memberships}

    def role_for(self, institution_id) -> str | None:
        return self.memberships.get(institution_id).role if institution_id in self.memberships else None

    def permissions_for(self, institution_id) -> set[str]:
        role = self.role_for(institution_id)
        return set(ROLE_PERMISSIONS.get(role, set()))


def get_auth(request: Request, db: Session = Depends(get_db)) -> AuthContext:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = header.removeprefix("Bearer ").strip()
    row = db.get(AuthToken, token)
    if row is None or row.expires_at < utcnow():
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, row.user_id)
    if user is None:
        raise HTTPException(401, "User no longer exists")
    memberships = db.scalars(
        select(InstitutionMembership).where(InstitutionMembership.user_id == user.id)
    ).all()
    return AuthContext(user, list(memberships))


def require_membership(auth: AuthContext, institution_id) -> str:
    role = auth.role_for(institution_id)
    if role is None:
        raise HTTPException(403, "No membership in this institution")
    return role


def require_permission(auth: AuthContext, institution_id, permission: str) -> None:
    role = require_membership(auth, institution_id)
    if permission not in ROLE_PERMISSIONS[role]:
        raise HTTPException(403, f"Role '{role}' lacks permission '{permission}'")
