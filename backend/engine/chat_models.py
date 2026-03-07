"""
Grok Chatbot FastAPI endpoint — /chat
"""
from fastapi import APIRouter
from pydantic import BaseModel
from engine.chatbot import chat_completion, build_travel_context
from typing import Optional

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    destination: Optional[str] = None
    user_profile: Optional[dict] = None


class ChatResponse(BaseModel):
    reply: str
    model: str
    tokens_used: int
    error: Optional[str] = None
