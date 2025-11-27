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
    Adventure, Event, ActionType
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

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO adventures (scenario_id, title, current_story_summary, memory)
            VALUES (?, ?, ?, ?)
        """, (
            scenario_id,
            title,
            scenario.plot.story_summary,
            scenario.plot.plot_essentials
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

        events = [
            Event(
                id=event["id"],
                adventure_id=event["adventure_id"],
                action_type=ActionType(event["action_type"]),
                player_input=event["player_input"],
                ai_response=event["ai_response"],
                created_at=event["created_at"]
            )
            for event in event_rows
        ]

        return Adventure(
            id=row["id"],
            scenario_id=row["scenario_id"],
            title=row["title"],
            current_story_summary=row["current_story_summary"],
            memory=row["memory"],
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

        return [
            Adventure(
                id=row["id"],
                scenario_id=row["scenario_id"],
                title=row["title"],
                current_story_summary=row["current_story_summary"],
                memory=row["memory"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]


def update_adventure(adventure_id: int, title: str = None,
                     current_story_summary: str = None, memory: str = None) -> Optional[Adventure]:
    """Update an adventure."""
    adventure = get_adventure(adventure_id)
    if not adventure:
        return None

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE adventures
            SET title = ?, current_story_summary = ?, memory = ?, updated_at = ?
            WHERE id = ?
        """, (
            title if title is not None else adventure.title,
            current_story_summary if current_story_summary is not None else adventure.current_story_summary,
            memory if memory is not None else adventure.memory,
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


# ============ Event Operations ============

def add_event(adventure_id: int, action_type: ActionType,
              player_input: str, ai_response: str) -> Event:
    """Add an event to an adventure's history."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (adventure_id, action_type, player_input, ai_response)
            VALUES (?, ?, ?, ?)
        """, (adventure_id, action_type.value, player_input, ai_response))

        event_id = cursor.lastrowid

        # Update adventure timestamp
        cursor.execute(
            "UPDATE adventures SET updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), adventure_id)
        )

        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        row = cursor.fetchone()

        return Event(
            id=row["id"],
            adventure_id=row["adventure_id"],
            action_type=ActionType(row["action_type"]),
            player_input=row["player_input"],
            ai_response=row["ai_response"],
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

        return [
            Event(
                id=row["id"],
                adventure_id=row["adventure_id"],
                action_type=ActionType(row["action_type"]),
                player_input=row["player_input"],
                ai_response=row["ai_response"],
                created_at=row["created_at"]
            )
            for row in reversed(rows)  # Reverse to get chronological order
        ]


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
