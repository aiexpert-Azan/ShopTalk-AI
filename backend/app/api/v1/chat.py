from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.azure_openai import ai_service
from typing import List

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = [] # List of {"role": "user"|"assistant", "content": "..."}

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Construct messages for OpenAI
    # Add system prompt based on business context if needed
    system_prompt = {"role": "system", "content": "You are a helpful assistant for ShopTalk-AI."}
    messages = [system_prompt] + request.history + [{"role": "user", "content": request.message}]
    
    response_text = await ai_service.get_chat_response(messages)
    return ChatResponse(response=response_text)
