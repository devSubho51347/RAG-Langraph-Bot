from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.db.models import User, Session, Message


async def get_user_by_username(
    db: AsyncSession, username: str
) -> Optional[User]:
    """Get a user by username."""
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    hashed_password: str
) -> User:
    """Create a new user."""
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_session(
    db: AsyncSession,
    user_id: UUID,
    title: str,
    expiration_hours: int = 1
) -> Session:
    """Create a new chat session."""
    session = Session(
        user_id=user_id,
        title=title,
        expires_at=datetime.utcnow() + timedelta(hours=expiration_hours)
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_active_session(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID
) -> Optional[Session]:
    """Get an active (non-expired) session."""
    query = (
        select(Session)
        .where(
            Session.id == session_id,
            Session.user_id == user_id,
            Session.expires_at > datetime.utcnow()
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_message(
    db: AsyncSession,
    session_id: UUID,
    role: str,
    content: str,
    context_chunks: Optional[str] = None
) -> Message:
    """Create a new message in a session."""
    message = Message(
        session_id=session_id,
        role=role,
        content=content,
        context_chunks=context_chunks
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_session_messages(
    db: AsyncSession,
    session_id: UUID,
    limit: int = 50
) -> List[Message]:
    """Get messages for a session, ordered by creation time."""
    query = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())
