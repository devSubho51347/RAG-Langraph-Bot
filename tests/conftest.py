import asyncio
import os
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)

from app.core.config import get_settings
from app.db.models import Base, User
from app.core.security import get_password_hash
from app.main import app

settings = get_settings()

# Test database URL
TEST_DB_URL = settings.DATABASE_URL.replace(
    settings.DATABASE_URL.split("/")[-1],
    f"test_db_{uuid4()}"
)

# Create async engine for tests
test_engine = create_async_engine(
    TEST_DB_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
    future=True
)

# Create async session factory
test_async_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Fixture for creating a test database."""
    # Create test database
    default_engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        isolation_level="AUTOCOMMIT"
    )
    
    async with default_engine.connect() as conn:
        database_name = TEST_DB_URL.split("/")[-1]
        await conn.execute(f'DROP DATABASE IF EXISTS {database_name}')
        await conn.execute(f'CREATE DATABASE {database_name}')
    
    await default_engine.dispose()
    
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    # Drop test database
    await test_engine.dispose()
    async with default_engine.connect() as conn:
        await conn.execute(f'DROP DATABASE {database_name}')
    await default_engine.dispose()


@pytest.fixture(scope="function")
async def db_session(
    test_db_engine: AsyncEngine
) -> AsyncGenerator[AsyncSession, None]:
    """Fixture for creating a new database session for a test."""
    async with test_async_session_factory() as session:
        yield session
        # Rollback any changes made in the test
        await session.rollback()
        # Clean up any rows that were added
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest.fixture(scope="function")
async def test_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Fixture for creating a test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> AsyncGenerator[User, None]:
    """Fixture for creating a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123")
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    yield user
