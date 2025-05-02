import pytest
import pytest_asyncio
import os
from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi import FastAPI
from dotenv import load_dotenv

from app.main import app, get_db
from app.models import Base

load_dotenv(".env.test")

test_engine = create_async_engine(
    os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
    ),
    echo=True,
    future=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="function")
def test_app() -> FastAPI:
    """Create a test instance of the FastAPI application."""
    return app


@pytest_asyncio.fixture(scope="function")
async def setup_database():
    """Set up the database before running tests."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(setup_database) -> AsyncSession:
    """Create a fresh database session for a test."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def client(test_app: FastAPI, db_session: AsyncSession) -> AsyncClient:
    """Create a test client with a fresh database session."""

    async def override_get_db():
        try:
            yield db_session
        finally:
            await db_session.rollback()
            await db_session.close()

    test_app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=test_app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as ac:
        yield ac

    test_app.dependency_overrides.clear()
