from typing import Dict, List, Any, Optional
from uuid import UUID
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolExecutor
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.vector_store import VectorStore, get_embeddings
from app.db.models import Message

settings = get_settings()


async def retrieve_context(
    state: Dict[str, Any],
    config: Optional[RunnableConfig] = None,
) -> Dict[str, Any]:
    """Retrieve relevant context using RAG."""
    # Get the latest message
    messages = state["messages"]
    latest_message = messages[-1].content if messages else ""
    
    # Get embeddings for the query
    query_embedding = await get_embeddings([latest_message])
    
    # Search vector store
    vector_store = VectorStore()
    results = await vector_store.similarity_search(
        query_embedding=query_embedding[0],
        session_id=state.get("session_id"),
        limit=3
    )
    
    # Update state with context
    state["context"] = "\n\n".join(r["text"] for r in results)
    return state


async def generate_response(
    state: Dict[str, Any],
    config: Optional[RunnableConfig] = None,
) -> Dict[str, Any]:
    """Generate response using context and chat history."""
    messages = state["messages"]
    context = state.get("context", "")
    
    # Create system message with context
    system_prompt = """You are a helpful AI assistant. Use the following context to answer the user's question.
    If you don't find relevant information in the context, say so.
    
    Context:
    {context}
    """
    
    # Initialize chat model
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        temperature=0.7,
        api_key=settings.OPENAI_API_KEY
    )
    
    # Convert messages to LangChain format
    lc_messages = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            lc_messages.append(HumanMessage(content=msg.content))
        elif isinstance(msg, AIMessage):
            lc_messages.append(AIMessage(content=msg.content))
    
    # Generate response
    response = await llm.ainvoke(
        [
            {
                "role": "system",
                "content": system_prompt.format(context=context)
            },
            *lc_messages
        ],
        config=config
    )
    
    # Update state
    state["response"] = response.content
    return state


async def save_message(
    state: Dict[str, Any],
    config: Optional[RunnableConfig] = None,
) -> Dict[str, Any]:
    """Save message to database."""
    if "db_session" not in state or "session_id" not in state:
        return state
    
    # Create new message
    message = Message(
        session_id=UUID(state["session_id"]),
        role="assistant",
        content=state["response"]
    )
    
    # Save to database
    state["db_session"].add(message)
    await state["db_session"].commit()
    await state["db_session"].refresh(message)
    
    return state
