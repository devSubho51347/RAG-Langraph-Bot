from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, AIMessage

from app.api.deps import get_current_user, get_db
from app.db.models import User, Session, Message
from app.db import crud
from app.rag.graph import create_chat_graph
from app.db.schemas import (
    ChatMessage,
    ChatResponse,
    ChatSession,
    ChatSessionCreate
)

router = APIRouter()


@router.post("/sessions", response_model=ChatSession)
async def create_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ChatSession:
    """Create a new chat session."""
    session = await crud.create_chat_session(db, current_user.id, session_data)
    return ChatSession.model_validate(session)


@router.get("/sessions", response_model=List[ChatSession])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ChatSession]:
    """List all chat sessions for current user."""
    sessions = await crud.get_user_chat_sessions(db, current_user.id)
    return [ChatSession.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ChatSession:
    """Get a specific chat session."""
    session = await crud.get_chat_session(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return ChatSession.model_validate(session)


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: UUID,
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """Send a message in a chat session."""
    # Verify session exists and belongs to user
    session = await crud.get_chat_session(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Save user message
    user_message = await crud.create_message(
        db,
        session_id=session_id,
        role="user",
        content=message.content
    )
    
    # Get chat history
    messages = await crud.get_session_messages(db, session_id)
    lc_messages = [
        HumanMessage(content=msg.content) if msg.role == "user"
        else AIMessage(content=msg.content)
        for msg in messages
    ]
    
    # Create and run chat graph
    chat_graph = create_chat_graph()
    result = await chat_graph.ainvoke({
        "messages": lc_messages,
        "session_id": str(session_id),
        "db_session": db
    })
    
    return ChatResponse(message=result["response"])
