"""
Database service for Lore CRUD operations.
"""
import json
from datetime import datetime
from typing import Optional

from database import get_db
from models.lore import (
    Scenario, ScenarioStatus, Plot,
    StoryCard, StoryCardType,
    Adventure, Event, ActionType,
    Scene, CharacterAction, CharacterState
)


# ============ Scenario Operations ============

def create_scenario(title: str, description: str = "", tags: list[str] = None,
                    plot: Plot = None) -> Scenario:
    """Create a new scenario."""
    tags = tags or []
    plot = plot or Plot()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scenarios (title, description, tags, plot, status)
            VALUES (?, ?, ?, ?, ?)
        """, (title, description, json.dumps(tags), json.dumps(plot.to_dict()), ScenarioStatus.DRAFT.value))

        scenario_id = cursor.lastrowid

    return get_scenario(scenario_id)


def get_scenario(scenario_id: int) -> Optional[Scenario]:
    """Get a scenario by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,))
        row = cursor.fetchone()

        if not row:
            return None

        # Get story cards for this scenario
        cursor.execute("SELECT * FROM story_cards WHERE scenario_id = ?", (scenario_id,))
        card_rows = cursor.fetchall()

        story_cards = [
            StoryCard(
                id=card["id"],
                scenario_id=card["scenario_id"],
                type=StoryCardType(card["type"]),
                name=card["name"],
                entry=card["entry"],
                triggers=json.loads(card["triggers"]),
                notes=card["notes"],
                created_at=card["created_at"],
                updated_at=card["updated_at"]
            )
            for card in card_rows
        ]

        return Scenario(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            tags=json.loads(row["tags"]),
            status=ScenarioStatus(row["status"]),
            plot=Plot.from_dict(json.loads(row["plot"])),
            story_cards=story_cards,
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )


def list_scenarios(status: ScenarioStatus = None) -> list[Scenario]:
    """List all scenarios, optionally filtered by status."""
    with get_db() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute(
                "SELECT * FROM scenarios WHERE status = ? ORDER BY updated_at DESC",
                (status.value,)
            )
        else:
            cursor.execute("SELECT * FROM scenarios ORDER BY updated_at DESC")

        rows = cursor.fetchall()

        return [
            Scenario(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                tags=json.loads(row["tags"]),
                status=ScenarioStatus(row["status"]),
                plot=Plot.from_dict(json.loads(row["plot"])),
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]


def update_scenario(scenario_id: int, title: str = None, description: str = None,
                    tags: list[str] = None, status: ScenarioStatus = None,
                    plot: Plot = None) -> Optional[Scenario]:
    """Update a scenario."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        return None

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE scenarios
            SET title = ?, description = ?, tags = ?, status = ?, plot = ?, updated_at = ?
            WHERE id = ?
        """, (
            title if title is not None else scenario.title,
            description if description is not None else scenario.description,
            json.dumps(tags if tags is not None else scenario.tags),
            (status.value if status else scenario.status.value),
            json.dumps((plot.to_dict() if plot else scenario.plot.to_dict())),
            datetime.now().isoformat(),
            scenario_id
        ))

    return get_scenario(scenario_id)


def delete_scenario(scenario_id: int) -> bool:
    """Delete a scenario and all associated data."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,))
        return cursor.rowcount > 0


# ============ Story Card Operations ============

def create_story_card(scenario_id: int, name: str, type: StoryCardType = StoryCardType.CUSTOM,
                      entry: str = "", triggers: list[str] = None, notes: str = "") -> StoryCard:
    """Create a new story card for a scenario."""
    triggers = triggers or []

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO story_cards (scenario_id, type, name, entry, triggers, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (scenario_id, type.value, name, entry, json.dumps(triggers), notes))

        card_id = cursor.lastrowid
        cursor.execute("SELECT * FROM story_cards WHERE id = ?", (card_id,))
        row = cursor.fetchone()

        return StoryCard(
            id=row["id"],
            scenario_id=row["scenario_id"],
            type=StoryCardType(row["type"]),
            name=row["name"],
            entry=row["entry"],
            triggers=json.loads(row["triggers"]),
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )


def get_story_card(card_id: int) -> Optional[StoryCard]:
    """Get a story card by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM story_cards WHERE id = ?", (card_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return StoryCard(
            id=row["id"],
            scenario_id=row["scenario_id"],
            type=StoryCardType(row["type"]),
            name=row["name"],
            entry=row["entry"],
            triggers=json.loads(row["triggers"]),
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )


def update_story_card(card_id: int, name: str = None, type: StoryCardType = None,
                      entry: str = None, triggers: list[str] = None, notes: str = None) -> Optional[StoryCard]:
    """Update a story card."""
    card = get_story_card(card_id)
    if not card:
        return None

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE story_cards
            SET name = ?, type = ?, entry = ?, triggers = ?, notes = ?, updated_at = ?
            WHERE id = ?
        """, (
            name if name is not None else card.name,
            (type.value if type else card.type.value),
            entry if entry is not None else card.entry,
            json.dumps(triggers if triggers is not None else card.triggers),
            notes if notes is not None else card.notes,
            datetime.now().isoformat(),
            card_id
        ))

    return get_story_card(card_id)


def delete_story_card(card_id: int) -> bool:
    """Delete a story card."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM story_cards WHERE id = ?", (card_id,))
        return cursor.rowcount > 0


def get_triggered_cards(scenario_id: int, text: str) -> list[StoryCard]:
    """Get story cards triggered by keywords in the given text."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM story_cards WHERE scenario_id = ?", (scenario_id,))
        rows = cursor.fetchall()

        triggered = []
        text_lower = text.lower()

        for row in rows:
            triggers = json.loads(row["triggers"])
            for trigger in triggers:
                if trigger.lower() in text_lower:
                    triggered.append(StoryCard(
                        id=row["id"],
                        scenario_id=row["scenario_id"],
                        type=StoryCardType(row["type"]),
                        name=row["name"],
                        entry=row["entry"],
                        triggers=triggers,
                        notes=row["notes"]
                    ))
                    break

        return triggered


# ============ Adventure Operations ============

def create_adventure(scenario_id: int, title: str = None) -> Adventure:
    """Create a new adventure from a scenario."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise ValueError(f"Scenario {scenario_id} not found")

    title = title or f"Adventure in {scenario.title}"

    # Create initial scene with PCs
    pcs = [card.name for card in scenario.story_cards if card.type == StoryCardType.PLAYING_CHARACTER]
    initial_scene = Scene(characters_present=pcs)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO adventures (scenario_id, title, current_story_summary, memory, current_scene)
            VALUES (?, ?, ?, ?, ?)
        """, (
            scenario_id,
            title,
            scenario.plot.story_summary,
            scenario.plot.plot_essentials,
            json.dumps(initial_scene.to_dict())
        ))

        adventure_id = cursor.lastrowid

    return get_adventure(adventure_id)


def get_adventure(adventure_id: int) -> Optional[Adventure]:
    """Get an adventure by ID with its event history."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM adventures WHERE id = ?", (adventure_id,))
        row = cursor.fetchone()

        if not row:
            return None

        # Get events for this adventure
        cursor.execute(
            "SELECT * FROM events WHERE adventure_id = ? ORDER BY created_at ASC",
            (adventure_id,)
        )
        event_rows = cursor.fetchall()

        events = []
        for event in event_rows:
            # Parse character actions
            char_actions_raw = json.loads(event["character_actions"] or "[]")
            char_actions = [CharacterAction.from_dict(ca) for ca in char_actions_raw]

            # Parse scene update
            scene_update = json.loads(event["scene_update"] or "{}") or None

            events.append(Event(
                id=event["id"],
                adventure_id=event["adventure_id"],
                action_type=ActionType(event["action_type"]),
                actor_name=event["actor_name"] or "",
                player_input=event["player_input"],
                narration=event["narration"] or "",
                character_actions=char_actions,
                scene_update=scene_update,
                created_at=event["created_at"]
            ))

        # Parse current scene
        current_scene_data = json.loads(row["current_scene"] or "{}")
        current_scene = Scene.from_dict(current_scene_data) if current_scene_data else None

        return Adventure(
            id=row["id"],
            scenario_id=row["scenario_id"],
            title=row["title"],
            current_story_summary=row["current_story_summary"],
            memory=row["memory"],
            current_scene=current_scene,
            history=events,
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )


def list_adventures(scenario_id: int = None) -> list[Adventure]:
    """List adventures, optionally filtered by scenario."""
    with get_db() as conn:
        cursor = conn.cursor()
        if scenario_id:
            cursor.execute(
                "SELECT * FROM adventures WHERE scenario_id = ? ORDER BY updated_at DESC",
                (scenario_id,)
            )
        else:
            cursor.execute("SELECT * FROM adventures ORDER BY updated_at DESC")

        rows = cursor.fetchall()

        adventures = []
        for row in rows:
            current_scene_data = json.loads(row["current_scene"] or "{}")
            current_scene = Scene.from_dict(current_scene_data) if current_scene_data else None

            adventures.append(Adventure(
                id=row["id"],
                scenario_id=row["scenario_id"],
                title=row["title"],
                current_story_summary=row["current_story_summary"],
                memory=row["memory"],
                current_scene=current_scene,
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            ))

        return adventures


def update_adventure(adventure_id: int, title: str = None,
                     current_story_summary: str = None, memory: str = None,
                     current_scene: Scene = None) -> Optional[Adventure]:
    """Update an adventure."""
    adventure = get_adventure(adventure_id)
    if not adventure:
        return None

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE adventures
            SET title = ?, current_story_summary = ?, memory = ?, current_scene = ?, updated_at = ?
            WHERE id = ?
        """, (
            title if title is not None else adventure.title,
            current_story_summary if current_story_summary is not None else adventure.current_story_summary,
            memory if memory is not None else adventure.memory,
            json.dumps(current_scene.to_dict() if current_scene else (adventure.current_scene.to_dict() if adventure.current_scene else {})),
            datetime.now().isoformat(),
            adventure_id
        ))

    return get_adventure(adventure_id)


def delete_adventure(adventure_id: int) -> bool:
    """Delete an adventure and its events."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM adventures WHERE id = ?", (adventure_id,))
        return cursor.rowcount > 0


# ============ Scene Operations ============

def update_scene(adventure_id: int, scene: Scene) -> Scene:
    """Update the current scene for an adventure."""
    scene.adventure_id = adventure_id
    scene.updated_at = datetime.now()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE adventures
            SET current_scene = ?, updated_at = ?
            WHERE id = ?
        """, (
            json.dumps(scene.to_dict()),
            datetime.now().isoformat(),
            adventure_id
        ))

    return scene


def get_characters_in_scene(adventure_id: int, scenario_id: int) -> dict:
    """Get all characters (PCs and NPCs) currently in the scene."""
    adventure = get_adventure(adventure_id)
    scenario = get_scenario(scenario_id)

    if not adventure or not scenario or not adventure.current_scene:
        return {"pcs": [], "npcs": []}

    present = adventure.current_scene.characters_present
    pcs = [c for c in scenario.story_cards if c.type == StoryCardType.PLAYING_CHARACTER and c.name in present]
    npcs = [c for c in scenario.story_cards if c.type == StoryCardType.CHARACTER and c.name in present]

    return {"pcs": pcs, "npcs": npcs}


def add_character_to_scene(adventure_id: int, character_name: str) -> Scene:
    """Add a character to the current scene."""
    adventure = get_adventure(adventure_id)
    if not adventure or not adventure.current_scene:
        raise ValueError("Adventure or scene not found")

    if character_name not in adventure.current_scene.characters_present:
        adventure.current_scene.characters_present.append(character_name)
        return update_scene(adventure_id, adventure.current_scene)

    return adventure.current_scene


def remove_character_from_scene(adventure_id: int, character_name: str) -> Scene:
    """Remove a character from the current scene."""
    adventure = get_adventure(adventure_id)
    if not adventure or not adventure.current_scene:
        raise ValueError("Adventure or scene not found")

    if character_name in adventure.current_scene.characters_present:
        adventure.current_scene.characters_present.remove(character_name)
        return update_scene(adventure_id, adventure.current_scene)

    return adventure.current_scene


# ============ Event Operations ============

def add_event(adventure_id: int, action_type: ActionType,
              player_input: str, narration: str = "",
              actor_name: str = "",
              character_actions: list[CharacterAction] = None,
              scene_update: dict = None) -> Event:
    """Add an event to an adventure's history."""
    character_actions = character_actions or []

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (adventure_id, action_type, actor_name, player_input, narration, character_actions, scene_update)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            adventure_id,
            action_type.value,
            actor_name,
            player_input,
            narration,
            json.dumps([ca.to_dict() for ca in character_actions]),
            json.dumps(scene_update or {})
        ))

        event_id = cursor.lastrowid

        # Update adventure timestamp
        cursor.execute(
            "UPDATE adventures SET updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), adventure_id)
        )

        # Apply scene updates if provided
        if scene_update:
            adventure = get_adventure(adventure_id)
            if adventure and adventure.current_scene:
                scene = adventure.current_scene
                if "location_name" in scene_update:
                    scene.location_name = scene_update["location_name"]
                if "location_description" in scene_update:
                    scene.location_description = scene_update["location_description"]
                if "characters_enter" in scene_update:
                    for char in scene_update["characters_enter"]:
                        if char not in scene.characters_present:
                            scene.characters_present.append(char)
                if "characters_exit" in scene_update:
                    for char in scene_update["characters_exit"]:
                        if char in scene.characters_present:
                            scene.characters_present.remove(char)
                if "situation" in scene_update:
                    scene.situation = scene_update["situation"]
                if "mood" in scene_update:
                    scene.mood = scene_update["mood"]
                if "time_of_day" in scene_update:
                    scene.time_of_day = scene_update["time_of_day"]
                update_scene(adventure_id, scene)

        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        row = cursor.fetchone()

        char_actions_raw = json.loads(row["character_actions"] or "[]")
        char_actions = [CharacterAction.from_dict(ca) for ca in char_actions_raw]

        return Event(
            id=row["id"],
            adventure_id=row["adventure_id"],
            action_type=ActionType(row["action_type"]),
            actor_name=row["actor_name"] or "",
            player_input=row["player_input"],
            narration=row["narration"] or "",
            character_actions=char_actions,
            scene_update=json.loads(row["scene_update"] or "{}") or None,
            created_at=row["created_at"]
        )


def get_recent_events(adventure_id: int, limit: int = 10) -> list[Event]:
    """Get the most recent events for an adventure."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM events
            WHERE adventure_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (adventure_id, limit))

        rows = cursor.fetchall()

        events = []
        for row in reversed(rows):  # Reverse to get chronological order
            char_actions_raw = json.loads(row["character_actions"] or "[]")
            char_actions = [CharacterAction.from_dict(ca) for ca in char_actions_raw]

            events.append(Event(
                id=row["id"],
                adventure_id=row["adventure_id"],
                action_type=ActionType(row["action_type"]),
                actor_name=row["actor_name"] or "",
                player_input=row["player_input"],
                narration=row["narration"] or "",
                character_actions=char_actions,
                scene_update=json.loads(row["scene_update"] or "{}") or None,
                created_at=row["created_at"]
            ))

        return events


def undo_last_event(adventure_id: int) -> bool:
    """Remove the last event from an adventure."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM events
            WHERE id = (
                SELECT id FROM events
                WHERE adventure_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            )
        """, (adventure_id,))
        return cursor.rowcount > 0


# ============ Character State Operations ============

def create_character_state(adventure_id: int, character_name: str,
                           character_card_id: int = None, is_pc: bool = False,
                           personality_traits: list[str] = None,
                           values: list[str] = None,
                           fears: list[str] = None,
                           speech_style: str = "",
                           inventory: list[dict] = None,
                           stats: dict = None) -> CharacterState:
    """Create a new character state for an adventure."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO character_states (
                adventure_id, character_name, character_card_id, is_pc,
                personality_traits, char_values, fears, speech_style,
                inventory, stats
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            adventure_id,
            character_name,
            character_card_id,
            1 if is_pc else 0,
            json.dumps(personality_traits or []),
            json.dumps(values or []),
            json.dumps(fears or []),
            speech_style,
            json.dumps(inventory or []),
            json.dumps(stats or {})
        ))

        state_id = cursor.lastrowid

    return get_character_state(state_id)


def get_character_state(state_id: int) -> Optional[CharacterState]:
    """Get a character state by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM character_states WHERE id = ?", (state_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return _row_to_character_state(row)


def get_character_state_by_name(adventure_id: int, character_name: str) -> Optional[CharacterState]:
    """Get a character state by adventure and character name."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM character_states WHERE adventure_id = ? AND character_name = ?",
            (adventure_id, character_name)
        )
        row = cursor.fetchone()

        if not row:
            return None

        return _row_to_character_state(row)


def list_character_states(adventure_id: int) -> list[CharacterState]:
    """List all character states for an adventure."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM character_states WHERE adventure_id = ? ORDER BY character_name",
            (adventure_id,)
        )
        rows = cursor.fetchall()

        return [_row_to_character_state(row) for row in rows]


def update_character_state(state_id: int, **kwargs) -> Optional[CharacterState]:
    """Update a character state. Accepts any CharacterState field as keyword argument."""
    state = get_character_state(state_id)
    if not state:
        return None

    # Build update query dynamically
    updates = []
    values = []

    field_mappings = {
        "personality_traits": (json.dumps, "personality_traits"),
        "values": (json.dumps, "char_values"),
        "fears": (json.dumps, "fears"),
        "speech_style": (str, "speech_style"),
        "current_mood": (str, "current_mood"),
        "current_goal": (str, "current_goal"),
        "long_term_goals": (json.dumps, "long_term_goals"),
        "inventory": (json.dumps, "inventory"),
        "equipped": (json.dumps, "equipped"),
        "relationships": (json.dumps, "relationships"),
        "stats": (json.dumps, "stats"),
        "recent_actions_summary": (str, "recent_actions_summary")
    }

    for field, (converter, db_field) in field_mappings.items():
        if field in kwargs:
            updates.append(f"{db_field} = ?")
            values.append(converter(kwargs[field]))

    if not updates:
        return state

    updates.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(state_id)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE character_states SET {', '.join(updates)} WHERE id = ?",
            values
        )

    return get_character_state(state_id)


def update_character_mood(adventure_id: int, character_name: str, mood: str) -> Optional[CharacterState]:
    """Quick update for character mood."""
    state = get_character_state_by_name(adventure_id, character_name)
    if state:
        return update_character_state(state.id, current_mood=mood)
    return None


def update_character_goal(adventure_id: int, character_name: str, goal: str) -> Optional[CharacterState]:
    """Quick update for character goal."""
    state = get_character_state_by_name(adventure_id, character_name)
    if state:
        return update_character_state(state.id, current_goal=goal)
    return None


def add_item_to_character(adventure_id: int, character_name: str,
                          item_name: str, description: str = "", quantity: int = 1) -> Optional[CharacterState]:
    """Add an item to a character's inventory."""
    state = get_character_state_by_name(adventure_id, character_name)
    if not state:
        return None

    state.add_item(item_name, description, quantity)
    return update_character_state(state.id, inventory=state.inventory)


def remove_item_from_character(adventure_id: int, character_name: str,
                               item_name: str, quantity: int = 1) -> Optional[CharacterState]:
    """Remove an item from a character's inventory."""
    state = get_character_state_by_name(adventure_id, character_name)
    if not state:
        return None

    if state.remove_item(item_name, quantity):
        return update_character_state(state.id, inventory=state.inventory, equipped=state.equipped)
    return state


def update_character_relationship(adventure_id: int, character_name: str,
                                   target_name: str, attitude: str, notes: str = "") -> Optional[CharacterState]:
    """Update a character's relationship with another character."""
    state = get_character_state_by_name(adventure_id, character_name)
    if not state:
        return None

    state.relationships[target_name] = {"attitude": attitude, "notes": notes}
    return update_character_state(state.id, relationships=state.relationships)


def get_character_action_history(adventure_id: int, character_name: str, limit: int = 20) -> list[CharacterAction]:
    """Get recent actions taken by a specific character."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT character_actions FROM events
            WHERE adventure_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (adventure_id, limit * 2))  # Fetch more to find enough for this character

        rows = cursor.fetchall()

        actions = []
        for row in reversed(rows):
            char_actions = json.loads(row["character_actions"] or "[]")
            for ca in char_actions:
                if ca.get("character_name") == character_name:
                    actions.append(CharacterAction.from_dict(ca))
                    if len(actions) >= limit:
                        break
            if len(actions) >= limit:
                break

        return actions


def initialize_character_states_for_adventure(adventure_id: int, scenario_id: int) -> list[CharacterState]:
    """Initialize character states for all characters in a scenario when starting an adventure."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        return []

    states = []
    for card in scenario.story_cards:
        if card.type in [StoryCardType.CHARACTER, StoryCardType.PLAYING_CHARACTER]:
            # Check if state already exists
            existing = get_character_state_by_name(adventure_id, card.name)
            if existing:
                states.append(existing)
                continue

            # Parse personality from card entry if structured
            # For now, create with defaults - user can edit later
            state = create_character_state(
                adventure_id=adventure_id,
                character_name=card.name,
                character_card_id=card.id,
                is_pc=(card.type == StoryCardType.PLAYING_CHARACTER)
            )
            states.append(state)

    return states


def _row_to_character_state(row) -> CharacterState:
    """Convert a database row to a CharacterState object."""
    return CharacterState(
        id=row["id"],
        adventure_id=row["adventure_id"],
        character_name=row["character_name"],
        character_card_id=row["character_card_id"],
        is_pc=bool(row["is_pc"]),
        personality_traits=json.loads(row["personality_traits"] or "[]"),
        values=json.loads(row["char_values"] or "[]"),
        fears=json.loads(row["fears"] or "[]"),
        speech_style=row["speech_style"] or "",
        current_mood=row["current_mood"] or "",
        current_goal=row["current_goal"] or "",
        long_term_goals=json.loads(row["long_term_goals"] or "[]"),
        inventory=json.loads(row["inventory"] or "[]"),
        equipped=json.loads(row["equipped"] or "[]"),
        relationships=json.loads(row["relationships"] or "{}"),
        stats=json.loads(row["stats"] or "{}"),
        recent_actions_summary=row["recent_actions_summary"] or "",
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )
