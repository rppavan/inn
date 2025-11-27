from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import pages, api
from routers import lore_pages, lore_api

app = FastAPI()

# Mount static files if needed (currently using CDN for HTMX/Tailwind)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Chat routes
app.include_router(pages.router)
app.include_router(api.router)

# Lore (role-playing/story writing) routes
app.include_router(lore_pages.router)
app.include_router(lore_api.router)
