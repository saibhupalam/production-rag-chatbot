from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.core.security import hash_password, verify_password


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email.ilike(email)).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username.ilike(username)).first()


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str
) -> User:
    """Create a new user with bcrypt-hashed password."""
    user = User(
        username=username.strip(),
        email=email.strip().lower(),
        hashed_password=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(
    db: Session,
    email_or_username: str,
    password: str
) -> Optional[User]:
    """Authenticate a user by email or username and password."""
    ident = email_or_username.strip().lower()
    user = db.query(User).filter(
        or_(
            User.email.ilike(ident),
            User.username.ilike(ident)
        )
    ).first()

    if not user:
        return None

    # Handle existing legacy test users without password hashes safely
    if not user.hashed_password:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
