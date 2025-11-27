from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.llm_service import get_chat_completion, update_settings

router = APIRouter(prefix="/api")

class SettingsUpdate(BaseModel):
    model: str
    api_base: str | None = None

class ChatMessage(BaseModel):
    message: str

@router.post("/settings")
async def update_settings_endpoint(data: SettingsUpdate):
    updated_settings = update_settings(data.model, data.api_base)
    return {"status": "success", "settings": updated_settings}

@router.post("/chat")
async def chat(data: ChatMessage):
    try:
        ai_content = await get_chat_completion(data.message)
        return {"role": "assistant", "content": ai_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
