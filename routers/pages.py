from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from state import settings
from services.llm_service import get_chat_completion, update_settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

@router.get("/settings", response_class=HTMLResponse)
async def get_settings(request: Request):
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "model": settings["model"],
        "api_base": settings["api_base"]
    })

@router.post("/settings", response_class=HTMLResponse)
async def update_settings_page(request: Request, model: str = Form(...), api_base: str = Form(None)):
    updated_settings = update_settings(model, api_base)

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "model": updated_settings["model"],
        "api_base": updated_settings["api_base"]
    })

@router.get("/chat", response_class=HTMLResponse)
async def get_chat(request: Request):
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "model": settings["model"]
    })

@router.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, message: str = Form(...)):
    user_message_html = templates.TemplateResponse("partials/user_message.html", {"request": request, "message": message}).body.decode("utf-8")

    try:
        ai_content = await get_chat_completion(message)
        ai_message_html = templates.TemplateResponse("partials/ai_message.html", {"request": request, "message": ai_content}).body.decode("utf-8")

        return HTMLResponse(content=user_message_html + ai_message_html)
    except Exception as e:
        error_html = templates.TemplateResponse("partials/error_message.html", {"request": request, "error": str(e)}).body.decode("utf-8")
        return HTMLResponse(content=user_message_html + error_html)
