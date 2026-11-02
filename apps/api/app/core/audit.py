from sqlalchemy.orm import Session

from ..models import AuditEvent


def audit(db: Session, *, action: str, actor_id=None, institution_id=None,
          application_id=None, target: str = "", before: dict | None = None,
          after: dict | None = None) -> None:
    db.add(AuditEvent(
        action=action, actor_id=actor_id, institution_id=institution_id,
        application_id=application_id, target=target,
        before=before or {}, after=after or {},
    ))
