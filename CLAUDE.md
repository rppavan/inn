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
  - **lore.py**: Lore entities (Scenario, Plot, StoryCard, Adventure, Event, Scene, CharacterState, CharacterAction)
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
- **Story Card**: Contextual entities with trigger keywords:
  - `pc` (Playing Character): User-controlled characters - AI never generates their dialogue
  - `character` (NPC): AI-controlled characters with individual voice generation
  - `location`, `item`, `faction`, `custom`: World-building elements
- **Scene**: Current state tracking (location, characters present, mood, situation)
- **Adventure**: A playthrough instance with scene state and event history
- **Event**: Structured record with narration, character actions (do/say), and scene updates
- **CharacterAction**: Structured response with action, speech, and optional inner thought

### Multi-LLM Orchestration

The adventure loop uses multiple LLM calls:

```
Player Action (as PC or Narrator)
        ↓
[1] Story Orchestrator (story_model)
    → Determines what happens in the world
    → Outputs JSON: narration, scene_update, which NPCs respond
        ↓
[2] For each responding NPC:
    Character Voice (character_model)
    → Generates that NPC's action/speech in their voice
        ↓
[3] Combine into structured Event
    → Save to database with scene updates
```

**Key distinction**: Playing Characters (PCs) are NEVER given AI-generated dialogue. The Story Orchestrator only determines world reactions to PC actions; users provide PC responses directly.

Configuration in `services/lore_llm_service.py`:
```python
lore_settings = {
    "api_base": "http://localhost:8080/v1",
    "story_model": "gemma-3-12b-it",      # For orchestration
    "character_model": "gemma-3-12b-it",  # For NPC voices
}
```

### Prompt Templates

Editable markdown files in `prompts/` directory:
- `story_orchestrator.md`: JSON-output prompt for determining world state and NPC responses
- `character_response.md`: JSON-output prompt for individual NPC dialogue/actions
- `story_director.md`: Narrative prompt for opening scenes
- `npc_creation.md`: Template for AI-generated character creation
- `story_summary_update.md`: Template for summarizing story progress

### Action Types

- **Do**: Physical action ("opens the door")
- **Say**: Dialogue ("Hello, innkeeper!")
- **Story**: Direct narration (narrator mode)
- **Do & Say**: Combined action and speech

### Scene Tracking

Each adventure maintains current scene state:
- `location_name`, `location_description`: Where the scene takes place
- `characters_present`: List of PC and NPC names currently in scene
- `situation`: Brief description of what's happening
- `mood`: Atmosphere (tense, relaxed, mysterious)
- `time_of_day`, `weather`: Environmental context

Scene updates happen automatically via `scene_update` in Story Orchestrator responses:
- `characters_enter`: NPCs joining the scene
- `characters_exit`: NPCs leaving the scene

### Character State Tracking

Each character (PC or NPC) has dynamic state tracked per adventure via `CharacterState`:

**Personality** (used by Character Voice for consistent portrayal):
- `personality_traits`: List of traits ("brave", "curious", "stubborn")
- `values`: What they care about
- `fears`: What worries them
- `speech_style`: How they talk (formal, gruff, dialect)

**Current State**:
- `current_mood`: Emotional state (updates based on story events)
- `current_goal`: Immediate objective
- `long_term_goals`: Bigger aspirations

**Inventory**:
- `inventory`: Items carried `[{name, description, quantity}]`
- `equipped`: Currently equipped item names

**Relationships**:
- `relationships`: `{character_name: {attitude, notes}}`

**Stats** (optional, for game-like scenarios):
- `stats`: Flexible dict like `{health: 100, mana: 50}`

Character states are:
- Initialized automatically when an adventure starts
- Included in LLM context for authentic responses
- Updated based on story orchestrator suggestions (mood changes)
- Displayed in the adventure sidebar (expandable character cards)

CRUD operations in `lore_db_service.py`:
- `create_character_state()`, `get_character_state_by_name()`, `list_character_states()`
- `update_character_mood()`, `update_character_goal()`
- `add_item_to_character()`, `remove_item_from_character()`
- `update_character_relationship()`
- `get_character_action_history()` - retrieve past actions by specific character

### Database

Lore uses SQLite (`lore.db`) with tables:
- `scenarios`: Adventure blueprints
- `story_cards`: Characters (PCs/NPCs), locations, items
- `adventures`: Playthrough instances with current_scene JSON
- `scenes`: Scene history (optional)
- `events`: Structured event history with narration and character_actions JSON
- `character_states`: Per-adventure character state (personality, inventory, relationships)

### API Endpoints

REST API at `/api/lore`:
- `GET/POST /scenarios` - List/create scenarios
- `GET/PUT/DELETE /scenarios/{id}` - Scenario CRUD
- `POST /scenarios/{id}/cards` - Add story cards
- `POST /scenarios/{id}/adventures` - Start new adventure
- `GET /adventures/{id}` - Get adventure with history and scene
- `POST /adventures/{id}/action` - Take action (includes actor_name for PC/narrator)
- `POST /adventures/{id}/undo` - Undo last action
- `GET/PUT /settings` - Lore LLM configuration
