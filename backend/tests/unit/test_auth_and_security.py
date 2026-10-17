import pytest
from datetime import timedelta
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)
from app.services.user_service import (
    create_user,
    authenticate_user,
    get_user_by_email,
    get_user_by_username
)
from app.models.user import User


def test_password_hashing():
    password = "MySecurePassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password(password, None) is False


def test_jwt_token_creation_and_decoding():
    user_id = 42
    token = create_access_token(subject=user_id)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == str(user_id)


def test_jwt_token_expired():
    user_id = 99
    # Expired token in the past
    token = create_access_token(subject=user_id, expires_delta=timedelta(seconds=-10))
    payload = decode_access_token(token)
    assert payload is None


def test_user_creation_and_authentication(db_session):
    user = create_user(
        db=db_session,
        username="alice",
        email="alice@example.com",
        password="alicepassword"
    )
    assert user.id is not None
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.hashed_password is not None

    # Authenticate with email
    auth_user = authenticate_user(db_session, "alice@example.com", "alicepassword")
    assert auth_user is not None
    assert auth_user.id == user.id

    # Authenticate with username
    auth_user_name = authenticate_user(db_session, "alice", "alicepassword")
    assert auth_user_name is not None
    assert auth_user_name.id == user.id

    # Fail with wrong password
    assert authenticate_user(db_session, "alice@example.com", "wrongpass") is None


def test_legacy_user_without_password_hash_cannot_login(db_session):
    # Simulates legacy pre-Phase 13 user without password hash
    legacy_user = User(
        username="legacy_sai",
        email="legacy@example.com",
        hashed_password=None
    )
    db_session.add(legacy_user)
    db_session.commit()

    # Must be safely blocked from logging in with blank or arbitrary password
    assert authenticate_user(db_session, "legacy@example.com", "") is None
    assert authenticate_user(db_session, "legacy@example.com", "password") is None
