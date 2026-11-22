from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.services.security import hash_password


def seed_default_user(db: Session) -> None:
    """Create one fictional admin account for development if no users exist yet."""
    if db.query(User).count() > 0:
        return
    db.add(
        User(
            username=settings.SEED_ADMIN_USERNAME,
            full_name=settings.SEED_ADMIN_NAME,
            hashed_password=hash_password(settings.SEED_ADMIN_PASSWORD),
            role="admin",
        )
    )
    db.commit()
