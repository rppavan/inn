"""
Lore pages router - handles HTML/HTMX endpoints for the role-playing feature.
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from models.lore import Plot, StoryCardType, ActionType, ScenarioStatus
from services import lore_db_service as db
from services import lore_llm_service as llm

router = APIRouter(prefix="/lore")
templates = Jinja2Templates(directory="templates")


# ============ Main Lore Page ============

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def lore_home(request: Request):
    """Lore home page - shows scenarios and adventures."""
    scenarios = db.list_scenarios()
    adventures = db.list_adventures()
    settings = llm.get_lore_settings()

    return templates.TemplateResponse("lore/home.html", {
        "request": request,
        "scenarios": scenarios,
        "adventures": adventures,
        "settings": settings
    })


# ============ Scenario Management ============

@router.get("/scenarios/new", response_class=HTMLResponse)
async def new_scenario_page(request: Request):
    """Page to create a new scenario."""
    return templates.TemplateResponse("lore/scenario_form.html", {
        "request": request,
        "scenario": None,
        "card_types": [t.value for t in StoryCardType]
    })


@router.post("/scenarios", response_class=HTMLResponse)
async def create_scenario(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    story: str = Form(""),
    ai_instructions: str = Form(""),
    story_summary: str = Form(""),
    plot_essentials: str = Form(""),
    authors_note: str = Form(""),
    third_person: bool = Form(False)
):
    """Create a new scenario."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    plot = Plot(
        story=story,
        ai_instructions=ai_instructions,
        story_summary=story_summary,
        plot_essentials=plot_essentials,
        authors_note=authors_note,
        third_person=third_person
    )

    scenario = db.create_scenario(title, description, tag_list, plot)

    return templates.TemplateResponse("lore/partials/scenario_created.html", {
        "request": request,
        "scenario": scenario
    })


@router.get("/scenarios/{scenario_id}", response_class=HTMLResponse)
async def view_scenario(request: Request, scenario_id: int):
    """View a scenario's details."""
    scenario = db.get_scenario(scenario_id)
    if not scenario:
        return HTMLResponse(content="Scenario not found", status_code=404)

    adventures = db.list_adventures(scenario_id)

    return templates.TemplateResponse("lore/scenario_detail.html", {
        "request": request,
        "scenario": scenario,
        "adventures": adventures,
        "card_types": [t.value for t in StoryCardType]
    })


@router.get("/scenarios/{scenario_id}/edit", response_class=HTMLResponse)
async def edit_scenario_page(request: Request, scenario_id: int):
    """Page to edit a scenario."""
    scenario = db.get_scenario(scenario_id)
    if not scenario:
        return HTMLResponse(content="Scenario not found", status_code=404)

    return templates.TemplateResponse("lore/scenario_form.html", {
        "request": request,
        "scenario": scenario,
        "card_types": [t.value for t in StoryCardType]
    })


@router.post("/scenarios/{scenario_id}", response_class=HTMLResponse)
async def update_scenario(
    request: Request,
    scenario_id: int,
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    status: str = Form("draft"),
    story: str = Form(""),
    ai_instructions: str = Form(""),
    story_summary: str = Form(""),
    plot_essentials: str = Form(""),
    authors_note: str = Form(""),
    third_person: bool = Form(False)
):
    """Update a scenario."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    plot = Plot(
        story=story,
        ai_instructions=ai_instructions,
        story_summary=story_summary,
        plot_essentials=plot_essentials,
        authors_note=authors_note,
        third_person=third_person
    )

    scenario = db.update_scenario(
        scenario_id,
        title=title,
        description=description,
        tags=tag_list,
        status=ScenarioStatus(status),
        plot=plot
    )

    if not scenario:
        return HTMLResponse(content="Scenario not found", status_code=404)

    return templates.TemplateResponse("lore/partials/scenario_updated.html", {
        "request": request,
        "scenario": scenario
    })


@router.delete("/scenarios/{scenario_id}", response_class=HTMLResponse)
async def delete_scenario(request: Request, scenario_id: int):
    """Delete a scenario."""
    success = db.delete_scenario(scenario_id)
    if success:
        return HTMLResponse(content="")
    return HTMLResponse(content="Failed to delete", status_code=400)


# ============ Story Card Management ============

@router.post("/scenarios/{scenario_id}/cards", response_class=HTMLResponse)
async def create_story_card(
    request: Request,
    scenario_id: int,
    name: str = Form(...),
    card_type: str = Form("custom"),
    entry: str = Form(""),
    triggers: str = Form(""),
    notes: str = Form("")
):
    """Create a new story card for a scenario."""
    trigger_list = [t.strip() for t in triggers.split(",") if t.strip()]

    card = db.create_story_card(
        scenario_id,
        name=name,
        type=StoryCardType(card_type),
        entry=entry,
        triggers=trigger_list,
        notes=notes
    )

    return templates.TemplateResponse("lore/partials/story_card.html", {
        "request": request,
        "card": card
    })


@router.delete("/cards/{card_id}", response_class=HTMLResponse)
async def delete_story_card(request: Request, card_id: int):
    """Delete a story card."""
    success = db.delete_story_card(card_id)
    if success:
        return HTMLResponse(content="")
    return HTMLResponse(content="Failed to delete", status_code=400)


# ============ Adventure Management ============

@router.post("/scenarios/{scenario_id}/play", response_class=HTMLResponse)
async def start_adventure(request: Request, scenario_id: int, title: str = Form(None)):
    """Start a new adventure from a scenario."""
    try:
        adventure = db.create_adventure(scenario_id, title)

        # Generate opening scene (now returns dict with narration, scene, etc.)
        result = await llm.generate_opening_scene(adventure.id)

        # Get updated adventure
        adventure = db.get_adventure(adventure.id)

        return templates.TemplateResponse("lore/partials/adventure_started.html", {
            "request": request,
            "adventure": adventure,
            "opening": result.get("narration", "")
        })
    except Exception as e:
        return templates.TemplateResponse("lore/partials/error.html", {
            "request": request,
            "error": str(e)
        })


@router.get("/adventures/{adventure_id}", response_class=HTMLResponse)
async def view_adventure(request: Request, adventure_id: int):
    """View an adventure."""
    adventure = db.get_adventure(adventure_id)
    if not adventure:
        return HTMLResponse(content="Adventure not found", status_code=404)

    scenario = db.get_scenario(adventure.scenario_id)

    # Get characters in scene
    chars_in_scene = db.get_characters_in_scene(adventure_id, scenario.id)

    # Get all PCs for the actor selector
    all_pcs = [c for c in scenario.story_cards if c.type == StoryCardType.PLAYING_CHARACTER]

    # Get character states for all characters
    character_states = db.list_character_states(adventure_id)
    char_state_map = {cs.character_name: cs for cs in character_states}

    return templates.TemplateResponse("lore/adventure.html", {
        "request": request,
        "adventure": adventure,
        "scenario": scenario,
        "pcs_in_scene": chars_in_scene.get("pcs", []),
        "npcs_in_scene": chars_in_scene.get("npcs", []),
        "all_pcs": all_pcs,
        "action_types": [t.value for t in ActionType],
        "character_states": char_state_map
    })


@router.post("/adventures/{adventure_id}/action", response_class=HTMLResponse)
async def take_action(
    request: Request,
    adventure_id: int,
    player_input: str = Form(...),
    action_type: str = Form("do"),
    actor_name: str = Form("")
):
    """Player takes an action in the adventure (can be narrator or a PC)."""
    try:
        result = await llm.continue_story(
            adventure_id,
            player_input,
            ActionType(action_type),
            actor_name=actor_name
        )

        # Get updated adventure for scene info
        adventure = db.get_adventure(adventure_id)

        return templates.TemplateResponse("lore/partials/story_response.html", {
            "request": request,
            "player_input": player_input,
            "action_type": action_type,
            "actor_name": actor_name,
            "result": result,
            "adventure": adventure
        })
    except Exception as e:
        return templates.TemplateResponse("lore/partials/error.html", {
            "request": request,
            "error": str(e)
        })


@router.post("/adventures/{adventure_id}/pc-action", response_class=HTMLResponse)
async def pc_action(
    request: Request,
    adventure_id: int,
    pc_name: str = Form(...),
    action: str = Form(""),
    speech: str = Form("")
):
    """A playing character takes an action or says something."""
    try:
        pc_action = await llm.add_pc_action(
            adventure_id,
            pc_name,
            action=action,
            speech=speech
        )

        return templates.TemplateResponse("lore/partials/pc_action.html", {
            "request": request,
            "pc_action": pc_action
        })
    except Exception as e:
        return templates.TemplateResponse("lore/partials/error.html", {
            "request": request,
            "error": str(e)
        })


@router.post("/adventures/{adventure_id}/undo", response_class=HTMLResponse)
async def undo_action(request: Request, adventure_id: int):
    """Undo the last action in an adventure."""
    success = db.undo_last_event(adventure_id)
    if success:
        adventure = db.get_adventure(adventure_id)
        return templates.TemplateResponse("lore/partials/history.html", {
            "request": request,
            "adventure": adventure
        })
    return HTMLResponse(content="Nothing to undo", status_code=400)


@router.delete("/adventures/{adventure_id}", response_class=HTMLResponse)
async def delete_adventure(request: Request, adventure_id: int):
    """Delete an adventure."""
    success = db.delete_adventure(adventure_id)
    if success:
        return HTMLResponse(content="")
    return HTMLResponse(content="Failed to delete", status_code=400)


# ============ Settings ============

@router.get("/settings", response_class=HTMLResponse)
async def lore_settings_page(request: Request):
    """Lore settings page."""
    settings = llm.get_lore_settings()
    return templates.TemplateResponse("lore/settings.html", {
        "request": request,
        "settings": settings
    })


@router.post("/settings", response_class=HTMLResponse)
async def update_lore_settings(
    request: Request,
    story_model: str = Form(...),
    character_model: str = Form(...),
    api_base: str = Form("")
):
    """Update lore settings."""
    settings = llm.update_lore_settings(story_model, character_model, api_base)
    return templates.TemplateResponse("lore/partials/settings_updated.html", {
        "request": request,
        "settings": settings
    })
