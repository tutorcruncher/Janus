import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import types, sys
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.dialects.postgresql import JSONB

from app.db.session import get_db
from sqlmodel import SQLModel, Session as SQLModelSession
from app.main import app
from app.utils.settings import get_settings

# Create test database – prefer ``TEST_DATABASE_URL`` so we don't touch the
# development database in any circumstance.  Fallback to the standard
# DATABASE_URL only if a dedicated test URL isn't supplied.

DATABASE_URL = os.getenv(
    'TEST_DATABASE_URL',
    os.getenv(
        'DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/eurus_test'
    ),
)
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(
    class_=SQLModelSession, autocommit=False, autoflush=False, bind=engine
)


@pytest.fixture(scope='function')
def db_session():
    SQLModel.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        SQLModel.metadata.drop_all(bind=engine)


@pytest.fixture(scope='function')
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope='function')
def settings():
    return get_settings()


@pytest.fixture(scope='function')
def test_env_vars(monkeypatch):
    """Set up test environment variables"""
    env_vars = {
        'DATABASE_URL': 'postgresql://postgres:postgres@localhost:5432/eurus',
        'TEST_DATABASE_URL': 'postgresql://postgres:postgres@localhost:5432/eurus_test',
        'LESSONSPACE_API_KEY': 'e002ad84-7708-4973-ab27-45d662673127',
        'API_KEY': 'test',
        'BASE_URL': 'http://localhost:8000',
        'LESSONSPACE_API_URL': 'https://api.thelessonspace.com/v2',
        'SENTRY_DSN': '',
        'LOGFIRE_TOKEN': '',
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
