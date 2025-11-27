"""
LLM service for the Lore feature with dual-model support.

Two LLMs are used:
1. Story Director - manages plot, narration, world-building
2. Character Voice - handles character dialogue and responses
"""
from pathlib import Path
from litellm import completion

from models.lore import ActionType, Adventure, StoryCard, Scenario, Plot
from services import lore_db_service as db

# Lore-specific LLM settings
lore_settings = {
    "api_base": "http://localhost:8080/v1",
    "story_model": "gemma-3-12b-it",  # Model for story direction
    "character_model": "gemma-3-12b-it",  # Model for character voices
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


def _build_story_context(adventure: Adventure, scenario: Scenario,
                         triggered_cards: list[StoryCard] = None) -> str:
    """Build the context string for story generation."""
    context_parts = []

    # Plot essentials
    if scenario.plot.plot_essentials:
        context_parts.append(f"### Plot Essentials\n{scenario.plot.plot_essentials}")

    # Story summary
    if adventure.current_story_summary:
        context_parts.append(f"### Story Summary\n{adventure.current_story_summary}")

    # Author's note
    if scenario.plot.authors_note:
        context_parts.append(f"### Author's Note\n{scenario.plot.authors_note}")

    # AI instructions
    if scenario.plot.ai_instructions:
        context_parts.append(f"### AI Instructions\n{scenario.plot.ai_instructions}")

    # Triggered story cards
    if triggered_cards:
        cards_text = "\n".join([
            f"**{card.name}** ({card.type.value}): {card.entry}"
            for card in triggered_cards
        ])
        context_parts.append(f"### Relevant Context\n{cards_text}")

    # Recent history
    recent_events = db.get_recent_events(adventure.id, limit=5)
    if recent_events:
        history_text = "\n".join([
            f"Player ({event.action_type.value}): {event.player_input}\n"
            f"Story: {event.ai_response[:200]}..."
            if len(event.ai_response) > 200 else
            f"Player ({event.action_type.value}): {event.player_input}\nStory: {event.ai_response}"
            for event in recent_events
        ])
        context_parts.append(f"### Recent Events\n{history_text}")

    return "\n\n".join(context_parts)


async def generate_opening_scene(adventure_id: int) -> str:
    """Generate the opening scene for a new adventure."""
    adventure = db.get_adventure(adventure_id)
    if not adventure:
        raise ValueError(f"Adventure {adventure_id} not found")

    scenario = db.get_scenario(adventure.scenario_id)
    if not scenario:
        raise ValueError(f"Scenario {adventure.scenario_id} not found")

    # Load system prompt
    system_prompt = _load_prompt("story_director.md")

    # Build context
    context_parts = [
        f"## Scenario: {scenario.title}",
        f"\n### Description\n{scenario.description}" if scenario.description else "",
        f"\n### Initial Story\n{scenario.plot.story}" if scenario.plot.story else "",
    ]

    if scenario.plot.plot_essentials:
        context_parts.append(f"\n### Plot Essentials\n{scenario.plot.plot_essentials}")

    if scenario.plot.ai_instructions:
        context_parts.append(f"\n### AI Instructions\n{scenario.plot.ai_instructions}")

    if scenario.plot.authors_note:
        context_parts.append(f"\n### Author's Note\n{scenario.plot.authors_note}")

    # Add story cards
    if scenario.story_cards:
        cards_text = "\n".join([
            f"- **{card.name}** ({card.type.value}): {card.entry}"
            for card in scenario.story_cards
        ])
        context_parts.append(f"\n### Available Story Cards\n{cards_text}")

    user_message = "\n".join(context_parts)
    user_message += "\n\n## Your Task\nGenerate an engaging opening scene for this adventure. Set the stage, hook the player, and present options for action."

    kwargs = _get_llm_kwargs("story")
    kwargs["messages"] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    response = completion(**kwargs)
    return response.choices[0].message.content


async def continue_story(adventure_id: int, player_input: str,
                         action_type: ActionType = ActionType.DO) -> str:
    """Continue the story based on player input."""
    adventure = db.get_adventure(adventure_id)
    if not adventure:
        raise ValueError(f"Adventure {adventure_id} not found")

    scenario = db.get_scenario(adventure.scenario_id)
    if not scenario:
        raise ValueError(f"Scenario {adventure.scenario_id} not found")

    # Check for triggered story cards
    triggered_cards = db.get_triggered_cards(scenario.id, player_input)

    # Load system prompt
    system_prompt = _load_prompt("story_director.md")

    # Build context
    context = _build_story_context(adventure, scenario, triggered_cards)

    # Format player action
    action_prefix = {
        ActionType.DO: "You",
        ActionType.SAY: "You say:",
        ActionType.STORY: ""
    }

    prefix = action_prefix.get(action_type, "You")
    formatted_action = f'{prefix} {player_input}' if prefix else player_input

    user_message = f"{context}\n\n## Current Action\n{formatted_action}\n\n## Your Task\nContinue the story based on this action."

    kwargs = _get_llm_kwargs("story")
    kwargs["messages"] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    response = completion(**kwargs)
    ai_response = response.choices[0].message.content

    # Save the event
    db.add_event(adventure_id, action_type, player_input, ai_response)

    return ai_response


async def generate_character_response(adventure_id: int, character_card: StoryCard,
                                      player_input: str, situation: str = "") -> str:
    """Generate a response from a specific character."""
    adventure = db.get_adventure(adventure_id)
    if not adventure:
        raise ValueError(f"Adventure {adventure_id} not found")

    # Load character voice system prompt
    system_prompt = _load_prompt("character_voice.md")

    # Build character context
    context_parts = [
        f"## Character: {character_card.name}",
        f"\n### Description\n{character_card.entry}",
    ]

    if character_card.notes:
        context_parts.append(f"\n### Notes\n{character_card.notes}")

    if situation:
        context_parts.append(f"\n### Current Situation\n{situation}")

    context_parts.append(f"\n### Player says/does\n{player_input}")

    user_message = "\n".join(context_parts)
    user_message += "\n\n## Your Task\nRespond as this character would. Include dialogue and brief action descriptions."

    kwargs = _get_llm_kwargs("character")
    kwargs["messages"] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    response = completion(**kwargs)
    return response.choices[0].message.content


async def create_npc(scenario_id: int, creation_context: str) -> dict:
    """Generate a new NPC based on context."""
    scenario = db.get_scenario(scenario_id)
    if not scenario:
        raise ValueError(f"Scenario {scenario_id} not found")

    # Load NPC creation prompt
    system_prompt = _load_prompt("npc_creation.md")

    # Get existing characters
    existing_chars = [
        card for card in scenario.story_cards
        if card.type.value == "character"
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
    new_events = "\n".join([
        f"- Player ({event.action_type.value}): {event.player_input}\n  Result: {event.ai_response[:150]}..."
        for event in recent_events[-5:]  # Last 5 events
    ])

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

    # Update the adventure
    db.update_adventure(adventure_id, current_story_summary=new_summary)

    return new_summary
