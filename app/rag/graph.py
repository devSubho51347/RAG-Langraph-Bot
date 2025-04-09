from typing import Dict, Any, Annotated, TypedDict
from uuid import UUID

from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor

from app.rag.nodes import retrieve_context, generate_response, save_message


class ChatState(TypedDict):
    """Type definition for chat state."""
    messages: list[BaseMessage]
    context: str
    response: str
    session_id: UUID


def create_chat_graph() -> StateGraph:
    """Create the chat workflow graph."""
    # Create graph
    workflow = StateGraph(ChatState)
    
    # Add nodes
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("generate", generate_response)
    workflow.add_node("save", save_message)
    
    # Define edges
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", "save")
    workflow.add_edge("save", END)
    
    # Set entry point
    workflow.set_entry_point("retrieve")
    
    return workflow.compile()
