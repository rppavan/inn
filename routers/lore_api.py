"""
Lore API router - REST API endpoints for the role-playing feature.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.lore import Plot, StoryCardType, ActionType, ScenarioStatus
from services import lore_db_service as db
from services import lore_llm_service as llm

router = APIRouter(prefix="/api/lore")


# ============ Pydantic Models ============

class PlotCreate(BaseModel):
    story: str = ""
    ai_instructions: str = ""
    story_summary: str = ""
    plot_essentials: str = ""
    authors_note: str = ""
    third_person: bool = False


class ScenarioCreate(BaseModel):
    title: str
    description: str = ""
    tags: list[str] = []
    plot: PlotCreate = PlotCreate()


class ScenarioUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    status: str | None = None
    plot: PlotCreate | None = None


class StoryCardCreate(BaseModel):
    name: str
    type: str = "custom"
    entry: str = ""
    triggers: list[str] = []
    notes: str = ""


class StoryCardUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    entry: str | None = None
    triggers: list[str] | None = None
    notes: str | None = None


class AdventureCreate(BaseModel):
    title: str | None = None


class ActionInput(BaseModel):
    player_input: str
    action_type: str = "do"


class NPCCreateRequest(BaseModel):
    creation_context: str


class SettingsUpdate(BaseModel):
    story_model: str | None = None
    character_model: str | None = None
    api_base: str | None = None


# ============ Scenario Endpoints ============

@router.get("/scenarios")
async def list_scenarios(status: str | None = None):
    """List all scenarios."""
    scenario_status = ScenarioStatus(status) if status else None
    scenarios = db.list_scenarios(scenario_status)
    return {"scenarios": [s.to_dict() for s in scenarios]}


@router.post("/scenarios")
async def create_scenario(data: ScenarioCreate):
    """Create a new scenario."""
    plot = Plot(
        story=data.plot.story,
        ai_instructions=data.plot.ai_instructions,
        story_summary=data.plot.story_summary,
        plot_essentials=data.plot.plot_essentials,
        authors_note=data.plot.authors_note,
        third_person=data.plot.third_person
    )
    scenario = db.create_scenario(data.title, data.description, data.tags, plot)
    return {"scenario": scenario.to_dict()}


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: int):
    """Get a scenario by ID."""
    scenario = db.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"scenario": scenario.to_dict(), "story_cards": [c.to_dict() for c in scenario.story_cards]}


@router.put("/scenarios/{scenario_id}")
async def update_scenario(scenario_id: int, data: ScenarioUpdate):
    """Update a scenario."""
    plot = None
    if data.plot:
        plot = Plot(
            story=data.plot.story,
            ai_instructions=data.plot.ai_instructions,
            story_summary=data.plot.story_summary,
            plot_essentials=data.plot.plot_essentials,
            authors_note=data.plot.authors_note,
            third_person=data.plot.third_person
        )

    status = ScenarioStatus(data.status) if data.status else None

    scenario = db.update_scenario(
        scenario_id,
        title=data.title,
        description=data.description,
        tags=data.tags,
        status=status,
        plot=plot
    )

    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return {"scenario": scenario.to_dict()}


@router.delete("/scenarios/{scenario_id}")
async def delete_scenario(scenario_id: int):
    """Delete a scenario."""
    success = db.delete_scenario(scenario_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"status": "deleted"}


# ============ Story Card Endpoints ============

@router.post("/scenarios/{scenario_id}/cards")
async def create_story_card(scenario_id: int, data: StoryCardCreate):
    """Create a story card for a scenario."""
    card = db.create_story_card(
        scenario_id,
        name=data.name,
        type=StoryCardType(data.type),
        entry=data.entry,
        triggers=data.triggers,
        notes=data.notes
    )
    return {"card": card.to_dict()}


@router.put("/cards/{card_id}")
async def update_story_card(card_id: int, data: StoryCardUpdate):
    """Update a story card."""
    card_type = StoryCardType(data.type) if data.type else None
    card = db.update_story_card(
        card_id,
        name=data.name,
        type=card_type,
        entry=data.entry,
        triggers=data.triggers,
        notes=data.notes
    )
    if not card:
        raise HTTPException(status_code=404, detail="Story card not found")
    return {"card": card.to_dict()}


@router.delete("/cards/{card_id}")
async def delete_story_card(card_id: int):
    """Delete a story card."""
    success = db.delete_story_card(card_id)
    if not success:
        raise HTTPException(status_code=404, detail="Story card not found")
    return {"status": "deleted"}


# ============ Adventure Endpoints ============

@router.get("/adventures")
async def list_adventures(scenario_id: int | None = None):
    """List adventures, optionally filtered by scenario."""
    adventures = db.list_adventures(scenario_id)
    return {"adventures": [a.to_dict() for a in adventures]}


@router.post("/scenarios/{scenario_id}/adventures")
async def create_adventure(scenario_id: int, data: AdventureCreate = AdventureCreate()):
    """Create a new adventure from a scenario."""
    try:
        adventure = db.create_adventure(scenario_id, data.title)
        return {"adventure": adventure.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/adventures/{adventure_id}")
async def get_adventure(adventure_id: int):
    """Get an adventure by ID."""
    adventure = db.get_adventure(adventure_id)
    if not adventure:
        raise HTTPException(status_code=404, detail="Adventure not found")
    return {
        "adventure": adventure.to_dict(),
        "history": [e.to_dict() for e in adventure.history]
    }


@router.delete("/adventures/{adventure_id}")
async def delete_adventure(adventure_id: int):
    """Delete an adventure."""
    success = db.delete_adventure(adventure_id)
    if not success:
        raise HTTPException(status_code=404, detail="Adventure not found")
    return {"status": "deleted"}


# ============ Game Play Endpoints ============

@router.post("/adventures/{adventure_id}/start")
async def start_adventure(adventure_id: int):
    """Generate the opening scene for an adventure."""
    try:
        opening = await llm.generate_opening_scene(adventure_id)
        db.add_event(adventure_id, ActionType.STORY, "[Adventure begins]", opening)
        return {"opening": opening}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adventures/{adventure_id}/action")
async def take_action(adventure_id: int, data: ActionInput):
    """Take an action in an adventure."""
    try:
        response = await llm.continue_story(
            adventure_id,
            data.player_input,
            ActionType(data.action_type)
        )
        return {"response": response}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adventures/{adventure_id}/undo")
async def undo_action(adventure_id: int):
    """Undo the last action in an adventure."""
    success = db.undo_last_event(adventure_id)
    if not success:
        raise HTTPException(status_code=400, detail="Nothing to undo")
    return {"status": "undone"}


@router.post("/adventures/{adventure_id}/summarize")
async def update_summary(adventure_id: int):
    """Update the story summary for an adventure."""
    try:
        summary = await llm.update_story_summary(adventure_id)
        return {"summary": summary}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ NPC Creation ============

@router.post("/scenarios/{scenario_id}/generate-npc")
async def generate_npc(scenario_id: int, data: NPCCreateRequest):
    """Generate a new NPC using AI."""
    try:
        result = await llm.create_npc(scenario_id, data.creation_context)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Settings Endpoints ============

@router.get("/settings")
async def get_settings():
    """Get lore settings."""
    return {"settings": llm.get_lore_settings()}


@router.put("/settings")
async def update_settings(data: SettingsUpdate):
    """Update lore settings."""
    settings = llm.update_lore_settings(
        story_model=data.story_model,
        character_model=data.character_model,
        api_base=data.api_base
    )
    return {"settings": settings}
