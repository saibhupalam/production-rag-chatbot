import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.dependencies import get_db
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.message import Message

# In-memory SQLite engine for fast, isolated, non-destructive testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=hash_password("password123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_user(db_session):
    user = User(
        username="otheruser",
        email="other@example.com",
        hashed_password=hash_password("secret456")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_headers(second_user):
    token = create_access_token(subject=second_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_document(db_session, test_user):
    doc = Document(
        filename="attention_paper.pdf",
        upload_status="processed",
        user_id=test_user.id
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


@pytest.fixture
def test_conversation(db_session, test_user, test_document):
    conv = Conversation(
        title="Discussion on Attention",
        user_id=test_user.id,
        document_id=test_document.id
    )
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)
    return conv
