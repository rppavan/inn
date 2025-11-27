"""
LLM service for the Lore feature with multi-LLM orchestration.

Two LLM roles:
1. Story Orchestrator - manages plot, narration, determines who responds
2. Character Voice - generates individual character dialogue/actions
"""
import json
import re
from pathlib import Path
from typing import Optional
from litellm import completion

from models.lore import (
    ActionType, Adventure, StoryCard, Scenario, Plot,
    Scene, CharacterAction, StoryCardType, CharacterState
)
from services import lore_db_service as db

# Lore-specific LLM settings
lore_settings = {
    "api_base": "http://localhost:8080/v1",
    "story_model": "qwen3-4B",      # Model for story orchestration
    "character_model": "gemma-2-9b",  # Model for character voices
}

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_path = PROMPTS_DIR / filename
    if prompt_path.exists():
        return prompt_path.read_text()
    return ""


def _get_llm_kwargs(model_type: str = "story") -> dict:
    """Get LLM kwargs based on model type."""
    model = lore_settings["story_model"] if model_type == "story" else lore_settings["character_model"]
    kwargs = {"model": model}

    if lore_settings["api_base"]:
        kwargs["api_base"] = lore_settings["api_base"]
        kwargs["custom_llm_provider"] = "openai"
        kwargs["api_key"] = "dummy"

    return kwargs


def update_lore_settings(story_model: str = None, character_model: str = None,
                         api_base: str = None) -> dict:
    """Update lore LLM settings."""
    if story_model:
        lore_settings["story_model"] = story_model
    if character_model:
        lore_settings["character_model"] = character_model
    if api_base is not None:
        lore_settings["api_base"] = api_base
    return lore_settings


def get_lore_settings() -> dict:
    """Get current lore settings."""
    return lore_settings.copy()


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try to find JSON in code blocks first
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try parsing the entire response as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in text
    brace_match = re.search(r'\{[\s\S]*\}', text)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return {}


def _build_context(adventure: Adventure, scenario: Scenario) -> str:
    """Build the context string for story generation."""
    context_parts = []

    # Current scene
    if adventure.current_scene:
        context_parts.append(f"## Current Scene\n{adventure.current_scene.describe()}")

    # Get all character states for this adventure
    character_states = db.list_character_states(adventure.id)
    state_map = {cs.character_name: cs for cs in character_states}

    # Characters info with states
    chars = db.get_characters_in_scene(adventure.id, scenario.id)
    if chars["pcs"]:
        pc_lines = []
        for c in chars["pcs"]:
            state = state_map.get(c.name)
            line = f"- **{c.name}** (PC): {c.entry}"
            if state:
                personality = state.describe_personality()
                current = state.describe_state()
                if personality:
                    line += f"\n  Personality: {personality}"
                if current:
                    line += f"\n  Current: {current}"
                if state.inventory:
                    items = [f"{i['name']} x{i.get('quantity', 1)}" for i in state.inventory[:5]]
                    line += f"\n  Inventory: {', '.join(items)}"
            pc_lines.append(line)
        context_parts.append(f"## Playing Characters Present\n" + "\n".join(pc_lines))

    if chars["npcs"]:
        npc_lines = []
        for c in chars["npcs"]:
            state = state_map.get(c.name)
            line = f"- **{c.name}** (NPC): {c.entry}"
            if state:
                personality = state.describe_personality()
                current = state.describe_state()
                if personality:
                    line += f"\n  Personality: {personality}"
                if current:
                    line += f"\n  Current: {current}"
                if state.relationships:
                    rel_str = ", ".join([f"{k}: {v.get('attitude', 'neutral')}" for k, v in list(state.relationships.items())[:3]])
                    line += f"\n  Relationships: {rel_str}"
            npc_lines.append(line)
        context_parts.append(f"## NPCs Present\n" + "\n".join(npc_lines))

    # Plot essentials
    if scenario.plot.plot_essentials:
        context_parts.append(f"## Plot Essentials\n{scenario.plot.plot_essentials}")

    # Story summary
    if adventure.current_story_summary:
        context_parts.append(f"## Story Summary\n{adventure.current_story_summary}")

    # AI instructions
    if scenario.plot.ai_instructions:
        context_parts.append(f"## AI Instructions\n{scenario.plot.ai_instructions}")

    # Author's note
    if scenario.plot.authors_note:
        context_parts.append(f"## Author's Note\n{scenario.plot.authors_note}")

    # Recent history
    recent_events = db.get_recent_events(adventure.id, limit=5)
    if recent_events:
        history_parts = []
        for event in recent_events:
            if event.actor_name:
                history_parts.append(f"**{event.actor_name}** ({event.action_type.value}): {event.player_input}")
            if event.narration:
                history_parts.append(f"*{event.narration[:150]}*")
            for ca in event.character_actions:
                if ca.speech:
                    history_parts.append(f"**{ca.character_name}**: \"{ca.speech}\"")
                if ca.action:
                    history_parts.append(f"*{ca.character_name} {ca.action}*")
        if history_parts:
            context_parts.append(f"## Recent Events\n" + "\n".join(history_parts[-10:]))

    return "\n\n".join(context_parts)


async def _call_story_orchestrator(context: str, player_action: str,
                                   actor_name: str, action_type: ActionType) -> dict:
    """Call the Story Orchestrator LLM to determine what happens."""
    system_prompt = _load_prompt("story_orchestrator.md")

    action_prefix = {
        ActionType.DO: f"{actor_name} attempts to",
        ActionType.SAY: f"{actor_name} says:",
        ActionType.STORY: "Narration:",
        ActionType.DO_SAY: f"{actor_name}"
    }
    prefix = action_prefix.get(action_type, actor_name)
    formatted_action = f"{prefix} {player_action}"

    user_message = f"""{context}

## Current Action
{formatted_action}

Respond with the JSON structure as specified. Remember:
- Write narration for environmental/non-dialogue events
- List which NPCs should respond
- Update scene state if anything changed
- Never write dialogue for any character"""

    kwargs = _get_llm_kwargs("story")
    kwargs["messages"] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    response = completion(**kwargs)
    response_text = response.choices[0].message.content

    result = _extract_json(response_text)

    # Ensure required fields exist
    if "narration" not in result:
        result["narration"] = response_text if not result else ""
    if "scene_update" not in result:
        result["scene_update"] = {}
    if "npc_responses" not in result:
        result["npc_responses"] = []
    if "pc_prompts" not in result:
        result["pc_prompts"] = []
    if "awaiting_pc_input" not in result:
        result["awaiting_pc_input"] = False

    return result


async def _call_character_voice(character: StoryCard, context: str,
                                response_context: str, mood: str = "",
                                adventure_id: int = None) -> CharacterAction:
    """Call the Character Voice LLM for a specific NPC."""
    system_prompt = _load_prompt("character_response.md")

    # Get character state if available
    state_info = ""
    if adventure_id:
        char_state = db.get_character_state_by_name(adventure_id, character.name)
        if char_state:
            state_parts = []
            if char_state.personality_traits:
                state_parts.append(f"Personality: {', '.join(char_state.personality_traits)}")
            if char_state.values:
                state_parts.append(f"Values: {', '.join(char_state.values)}")
            if char_state.fears:
                state_parts.append(f"Fears: {', '.join(char_state.fears)}")
            if char_state.speech_style:
                state_parts.append(f"Speech style: {char_state.speech_style}")
            if char_state.current_goal:
                state_parts.append(f"Current goal: {char_state.current_goal}")
            if char_state.inventory:
                items = [i['name'] for i in char_state.inventory[:5]]
                state_parts.append(f"Carrying: {', '.join(items)}")
            if char_state.relationships:
                rels = [f"{k} ({v.get('attitude', 'neutral')})" for k, v in list(char_state.relationships.items())[:3]]
                state_parts.append(f"Relationships: {', '.join(rels)}")
            if state_parts:
                state_info = "\n".join(state_parts)

    user_message = f"""## Character: {character.name}

### Description
{character.entry}

### Character Notes
{character.notes or "None provided"}

### Character State
{state_info or "No detailed state available"}

### Current Mood
{mood or "Neutral"}

### Situation Context
{context}

### What to respond to
{response_context}

Respond with the JSON structure as specified."""

    kwargs = _get_llm_kwargs("character")
    kwargs["messages"] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    response = completion(**kwargs)
    response_text = response.choices[0].message.content

    result = _extract_json(response_text)

    return CharacterAction(
        character_name=character.name,
        character_id=character.id,
        action=result.get("action", ""),
        speech=result.get("speech", ""),
        inner_thought=result.get("inner_thought", ""),
        is_pc=False
    )


async def generate_opening_scene(adventure_id: int) -> dict:
    """Generate the opening scene for a new adventure."""
    adventure = db.get_adventure(adventure_id)
    if not adventure:
        raise ValueError(f"Adventure {adventure_id} not found")

    scenario = db.get_scenario(adventure.scenario_id)
    if not scenario:
        raise ValueError(f"Scenario {adventure.scenario_id} not found")

    # Use the simple story director for opening
    system_prompt = _load_prompt("story_director.md")

    # Build initial context
    pcs = [c for c in scenario.story_cards if c.type == StoryCardType.PLAYING_CHARACTER]
    npcs = [c for c in scenario.story_cards if c.type == StoryCardType.CHARACTER]
    locations = [c for c in scenario.story_cards if c.type == StoryCardType.LOCATION]

    context_parts = [
        f"## Scenario: {scenario.title}",
        f"\n### Description\n{scenario.description}" if scenario.description else "",
        f"\n### Initial Story\n{scenario.plot.story}" if scenario.plot.story else "",
    ]

    if pcs:
        pc_text = "\n".join([f"- {c.name}: {c.entry}" for c in pcs])
        context_parts.append(f"\n### Playing Characters\n{pc_text}")

    if npcs:
        npc_text = "\n".join([f"- {c.name}: {c.entry}" for c in npcs])
        context_parts.append(f"\n### NPCs\n{npc_text}")

    if locations:
        loc_text = "\n".join([f"- {c.name}: {c.entry}" for c in locations])
        context_parts.append(f"\n### Locations\n{loc_text}")

    if scenario.plot.ai_instructions:
        context_parts.append(f"\n### AI Instructions\n{scenario.plot.ai_instructions}")

    user_message = "\n".join(context_parts)
    user_message += "\n\n## Your Task\nGenerate an engaging opening scene. Set the stage, describe the environment, and present a situation for the players."

    kwargs = _get_llm_kwargs("story")
    kwargs["messages"] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    response = completion(**kwargs)
    opening_narration = response.choices[0].message.content

    # Set up initial scene
    initial_scene = Scene(
        adventure_id=adventure_id,
        location_name=locations[0].name if locations else "Unknown Location",
        location_description=locations[0].entry if locations else "",
        characters_present=[c.name for c in pcs],
        situation="The adventure begins..."
    )
    db.update_scene(adventure_id, initial_scene)

    # Initialize character states for all characters in the scenario
    db.initialize_character_states_for_adventure(adventure_id, scenario.id)

    # Save opening as first event
    db.add_event(
        adventure_id=adventure_id,
        action_type=ActionType.STORY,
        player_input="[Adventure begins]",
        narration=opening_narration,
        actor_name="",
        character_actions=[],
        scene_update=initial_scene.to_dict()
    )

    return {
        "narration": opening_narration,
        "scene": initial_scene.to_dict(),
        "awaiting_pc_input": True
    }


async def continue_story(adventure_id: int, player_input: str,
                         action_type: ActionType = ActionType.DO,
                         actor_name: str = "") -> dict:
    """
    Continue the story based on player input using multi-LLM orchestration.

    Flow:
    1. Story Orchestrator determines what happens and who responds
    2. Character Voice is called for each NPC that should respond
    3. Results are combined and returned

    Returns dict with:
    - narration: Environmental/non-dialogue narrative
    - character_actions: List of NPC responses
    - scene_update: Any scene changes
    - pc_prompts: Prompts for PC input (if any)
    - awaiting_pc_input: Whether we need PC response to continue
    """
    adventure = db.get_adventure(adventure_id)
    if not adventure:
        raise ValueError(f"Adventure {adventure_id} not found")

    scenario = db.get_scenario(adventure.scenario_id)
    if not scenario:
        raise ValueError(f"Scenario {adventure.scenario_id} not found")

    # Build context
    context = _build_context(adventure, scenario)

    # Step 1: Call Story Orchestrator
    orchestrator_result = await _call_story_orchestrator(
        context, player_input, actor_name, action_type
    )

    narration = orchestrator_result.get("narration", "")
    scene_update = orchestrator_result.get("scene_update", {})
    npc_responses = orchestrator_result.get("npc_responses", [])
    pc_prompts = orchestrator_result.get("pc_prompts", [])
    awaiting_pc_input = orchestrator_result.get("awaiting_pc_input", False)

    # Step 2: Generate NPC responses
    character_actions = []

    # Get NPCs in scene
    chars_in_scene = db.get_characters_in_scene(adventure_id, scenario.id)
    npc_map = {npc.name: npc for npc in chars_in_scene["npcs"]}

    for npc_response in npc_responses:
        npc_name = npc_response.get("character_name", "")
        should_respond = npc_response.get("should_respond", False)

        if should_respond and npc_name in npc_map:
            npc_card = npc_map[npc_name]
            response_context = npc_response.get("response_context", player_input)
            mood = npc_response.get("suggested_mood", "")

            # Call Character Voice for this NPC
            char_action = await _call_character_voice(
                npc_card, context, response_context, mood, adventure_id
            )
            character_actions.append(char_action)

            # Update character mood if provided
            if mood:
                db.update_character_mood(adventure_id, npc_name, mood)

    # Step 3: Save the event
    db.add_event(
        adventure_id=adventure_id,
        action_type=action_type,
        player_input=player_input,
        narration=narration,
        actor_name=actor_name,
        character_actions=character_actions,
        scene_update=scene_update if scene_update else None
    )

    return {
        "narration": narration,
        "character_actions": [ca.to_dict() for ca in character_actions],
        "scene_update": scene_update,
        "pc_prompts": pc_prompts,
        "awaiting_pc_input": awaiting_pc_input
    }


async def add_pc_action(adventure_id: int, pc_name: str,
                        action: str = "", speech: str = "") -> CharacterAction:
    """Add a Playing Character's action/speech to the story."""
    adventure = db.get_adventure(adventure_id)
    if not adventure:
        raise ValueError(f"Adventure {adventure_id} not found")

    scenario = db.get_scenario(adventure.scenario_id)
    if not scenario:
        raise ValueError(f"Scenario {adventure.scenario_id} not found")

    # Find the PC
    pc_card = None
    for card in scenario.story_cards:
        if card.type == StoryCardType.PLAYING_CHARACTER and card.name == pc_name:
            pc_card = card
            break

    if not pc_card:
        raise ValueError(f"Playing character {pc_name} not found")

    # Create the PC action
    pc_action = CharacterAction(
        character_name=pc_name,
        character_id=pc_card.id,
        action=action,
        speech=speech,
        is_pc=True
    )

    # Determine action type
    if action and speech:
        action_type = ActionType.DO_SAY
        player_input = f"{action} \"{speech}\""
    elif speech:
        action_type = ActionType.SAY
        player_input = speech
    else:
        action_type = ActionType.DO
        player_input = action

    # Save as an event (no narration, just the PC action)
    db.add_event(
        adventure_id=adventure_id,
        action_type=action_type,
        player_input=player_input,
        narration="",
        actor_name=pc_name,
        character_actions=[pc_action],
        scene_update=None
    )

    return pc_action


async def create_npc(scenario_id: int, creation_context: str) -> dict:
    """Generate a new NPC based on context."""
    scenario = db.get_scenario(scenario_id)
    if not scenario:
        raise ValueError(f"Scenario {scenario_id} not found")

    system_prompt = _load_prompt("npc_creation.md")

    existing_chars = [
        card for card in scenario.story_cards
        if card.type == StoryCardType.CHARACTER
    ]
    existing_chars_text = ", ".join([c.name for c in existing_chars]) if existing_chars else "None yet"

    context_parts = [
        f"## Setting\n{scenario.description}" if scenario.description else "",
        f"\n## Story Context\n{scenario.plot.story_summary}" if scenario.plot.story_summary else "",
        f"\n## Existing Characters\n{existing_chars_text}",
        f"\n## Creation Request\n{creation_context}",
    ]

    user_message = "\n".join(filter(None, context_parts))
    user_message += "\n\n## Your Task\nCreate a new character that fits this world and context."

    kwargs = _get_llm_kwargs("story")
    kwargs["messages"] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    response = completion(**kwargs)
    return {"raw_response": response.choices[0].message.content}


async def update_story_summary(adventure_id: int) -> str:
    """Update the story summary based on recent events."""
    adventure = db.get_adventure(adventure_id)
    if not adventure:
        raise ValueError(f"Adventure {adventure_id} not found")

    recent_events = db.get_recent_events(adventure_id, limit=10)
    if not recent_events:
        return adventure.current_story_summary

    # Format new events
    event_summaries = []
    for event in recent_events[-5:]:
        parts = []
        if event.actor_name and event.player_input:
            parts.append(f"- {event.actor_name}: {event.player_input}")
        if event.narration:
            parts.append(f"  {event.narration[:100]}...")
        for ca in event.character_actions:
            if ca.speech:
                parts.append(f"  {ca.character_name}: \"{ca.speech[:50]}...\"")
        event_summaries.append("\n".join(parts))

    new_events = "\n".join(event_summaries)

    system_prompt = "You are a narrative analyst. Create concise story summaries that preserve important details."

    user_message = f"""## Current Summary
{adventure.current_story_summary or "The adventure has just begun."}

## New Events
{new_events}

## Your Task
Update the story summary to incorporate these new events. Keep it under 300 words and focus on key plot points, character developments, and unresolved threads."""

    kwargs = _get_llm_kwargs("story")
    kwargs["messages"] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    response = completion(**kwargs)
    new_summary = response.choices[0].message.content

    db.update_adventure(adventure_id, current_story_summary=new_summary)

    return new_summary
