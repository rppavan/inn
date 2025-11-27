# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based web application with two main features:
1. **Chat**: A simple chat interface for interacting with local LLM models
2. **Lore**: A role-playing/story writing feature inspired by AI Dungeon

The application uses HTMX for dynamic UI updates, Jinja2 templates for server-side rendering, and connects to local LLMs via Ollama or similar OpenAI-compatible endpoints.

## Development Commands

### Start the development server
```bash
uv run fastapi dev
```
The server will be available at http://localhost:8000

### Run tests
```bash
pytest test_app.py
```

## Architecture

### Application Structure

The application follows a layered FastAPI architecture with proper separation of concerns:

- **main.py**: Entry point that creates the FastAPI app and includes routers
- **state.py**: Global application state (in-memory settings for model configuration)
- **database.py**: SQLite database initialization and connection management for Lore
- **models/**: Data models
  - **lore.py**: Lore entities (Scenario, Plot, StoryCard, Adventure, Event)
- **services/**: Business logic layer
  - **llm_service.py**: Chat LLM interaction and settings management
  - **lore_db_service.py**: Lore database CRUD operations
  - **lore_llm_service.py**: Lore LLM service with dual-model support
- **routers/**: HTTP layer - handles request/response formatting
  - **api.py**: Chat REST API endpoints
  - **pages.py**: Chat HTML/HTMX endpoints
  - **lore_api.py**: Lore REST API endpoints (`/api/lore/*`)
  - **lore_pages.py**: Lore HTML/HTMX endpoints (`/lore/*`)
- **prompts/**: Editable LLM prompt templates (markdown files)
- **templates/**: Jinja2 templates for server-side rendering
  - **base.html**: Main layout/navigation
  - **chat.html**: Chat interface
  - **settings.html**: Model configuration page
  - **partials/**: Chat HTMX partial templates
  - **lore/**: Lore templates (home, scenarios, adventures, settings)
  - **lore/partials/**: Lore HTMX partial templates

### LLM Integration

The application uses LiteLLM (`litellm` package) to interact with LLM models:

- Supports any OpenAI-compatible API endpoint (configured via `api_base` setting)
- Default model: `gemma-3-12b-it` with local endpoint at `http://localhost:8080/v1`
- When `api_base` is set, uses `custom_llm_provider="openai"` with `api_key="dummy"`
- All LLM interaction logic is centralized in `services/llm_service.py`:
  - `get_chat_completion(message)`: Handles chat completion with configured model
  - `update_settings(model, api_base)`: Updates application settings

### State Management

Settings are stored in-memory via `state.py`:
- `model`: The LLM model identifier
- `api_base`: The API endpoint URL (optional)

**Important**: Settings are not persisted; they reset when the server restarts.

### Router Separation of Concerns

The routers follow a clear separation:

- **api.py**: Pure REST API - accepts/returns JSON, intended for programmatic access
- **pages.py**: HTML/HTMX interface - accepts form data, returns rendered HTML templates

Both routers call the same `services/llm_service.py` functions for business logic, ensuring no code duplication while maintaining different response formats.

### Frontend Architecture

The UI uses:
- **HTMX**: For dynamic partial page updates without full page reloads
- **Tailwind CSS**: Via CDN for styling
- **Jinja2 Templates**: Server-side rendering with HTMX integration

The chat endpoint (`POST /chat`) returns concatenated HTML partials (user message + AI response) that HTMX appends to the chat container.

## Lore Feature (Role-Playing/Story Writing)

The Lore feature at `/lore` provides an AI Dungeon-style interactive story experience.

### Core Concepts

- **Scenario**: Blueprint for an adventure containing title, description, tags, plot configuration, and story cards
- **Plot**: Initial story context including opening text, AI instructions, plot essentials, and author's note
- **Story Card**: Contextual entities (characters, locations, items, factions) with trigger keywords that inject content when mentioned
- **Adventure**: A playthrough instance of a scenario with event history
- **Event**: A player action and AI response pair in the adventure history

### Dual-LLM Architecture

Lore uses two LLM roles (can be same or different models):
- **Story Director**: Manages narrative, world-building, plot progression, and NPC behavior
- **Character Voice**: Handles character dialogue and personality-driven responses

Configuration is in `services/lore_llm_service.py`:
```python
lore_settings = {
    "api_base": "http://localhost:8080/v1",
    "story_model": "gemma-3-12b-it",
    "character_model": "gemma-3-12b-it",
}
```

### Prompt Templates

Editable markdown files in `prompts/` directory:
- `story_director.md`: System prompt for narrative management
- `character_voice.md`: System prompt for character dialogue
- `story_continuation.md`: Template for continuing stories based on player actions
- `npc_creation.md`: Template for AI-generated character creation
- `story_summary_update.md`: Template for summarizing story progress
- `opening_scene.md`: Template for generating adventure openings

### Action Types

Players interact using three action types:
- **Do**: Perform an action ("I open the door")
- **Say**: Speak as the character ("Hello, innkeeper!")
- **Story**: Direct narration ("The sun sets over the mountains")

### Database

Lore uses SQLite (`lore.db`) with tables:
- `scenarios`: Adventure blueprints
- `story_cards`: Contextual entities linked to scenarios
- `adventures`: Playthrough instances
- `events`: Action/response history

### API Endpoints

REST API at `/api/lore`:
- `GET/POST /scenarios` - List/create scenarios
- `GET/PUT/DELETE /scenarios/{id}` - Scenario CRUD
- `POST /scenarios/{id}/cards` - Add story cards
- `POST /scenarios/{id}/adventures` - Start new adventure
- `GET /adventures/{id}` - Get adventure with history
- `POST /adventures/{id}/action` - Take player action
- `POST /adventures/{id}/undo` - Undo last action
- `GET/PUT /settings` - Lore LLM configuration
