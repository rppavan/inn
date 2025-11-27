"""
Lore database models for role-playing/story writing feature.
Based on AI Dungeon-style entities with multi-LLM support.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import json


class ScenarioStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    UNAVAILABLE = "unavailable"


class StoryCardType(str, Enum):
    CHARACTER = "character"          # NPC - AI controlled
    PLAYING_CHARACTER = "pc"         # PC - User controlled
    LOCATION = "location"
    ITEM = "item"
    CLASS = "class"
    RACE = "race"
    FACTION = "faction"
    CUSTOM = "custom"


class ActionType(str, Enum):
    DO = "do"           # Performs an action
    SAY = "say"         # Says something
    STORY = "story"     # Direct narration
    DO_SAY = "do_say"   # Combined action and speech


@dataclass
class CharacterState:
    """Tracks the dynamic state of a character during an adventure."""
    id: Optional[int] = None
    adventure_id: Optional[int] = None
    character_name: str = ""
    character_card_id: Optional[int] = None  # Reference to StoryCard
    is_pc: bool = False

    # Personality (structured traits)
    personality_traits: list[str] = field(default_factory=list)  # e.g., ["brave", "curious", "stubborn"]
    values: list[str] = field(default_factory=list)              # What they care about
    fears: list[str] = field(default_factory=list)               # What they fear
    speech_style: str = ""                                        # How they talk

    # Current state
    current_mood: str = ""                    # Current emotional state
    current_goal: str = ""                    # What they're trying to do right now
    long_term_goals: list[str] = field(default_factory=list)

    # Inventory
    inventory: list[dict] = field(default_factory=list)  # [{name, description, quantity}]
    equipped: list[str] = field(default_factory=list)    # Currently equipped item names

    # Relationships
    relationships: dict = field(default_factory=dict)  # {character_name: {attitude, notes}}

    # Stats (optional, for game-like scenarios)
    stats: dict = field(default_factory=dict)  # Flexible stats like {health: 100, mana: 50}

    # History summary
    recent_actions_summary: str = ""  # AI-generated summary of recent actions

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "adventure_id": self.adventure_id,
            "character_name": self.character_name,
            "character_card_id": self.character_card_id,
            "is_pc": self.is_pc,
            "personality_traits": self.personality_traits,
            "values": self.values,
            "fears": self.fears,
            "speech_style": self.speech_style,
            "current_mood": self.current_mood,
            "current_goal": self.current_goal,
            "long_term_goals": self.long_term_goals,
            "inventory": self.inventory,
            "equipped": self.equipped,
            "relationships": self.relationships,
            "stats": self.stats,
            "recent_actions_summary": self.recent_actions_summary
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CharacterState":
        return cls(
            id=data.get("id"),
            adventure_id=data.get("adventure_id"),
            character_name=data.get("character_name", ""),
            character_card_id=data.get("character_card_id"),
            is_pc=data.get("is_pc", False),
            personality_traits=data.get("personality_traits", []),
            values=data.get("values", []),
            fears=data.get("fears", []),
            speech_style=data.get("speech_style", ""),
            current_mood=data.get("current_mood", ""),
            current_goal=data.get("current_goal", ""),
            long_term_goals=data.get("long_term_goals", []),
            inventory=data.get("inventory", []),
            equipped=data.get("equipped", []),
            relationships=data.get("relationships", {}),
            stats=data.get("stats", {}),
            recent_actions_summary=data.get("recent_actions_summary", "")
        )

    def describe_personality(self) -> str:
        """Generate a personality description for LLM context."""
        parts = []
        if self.personality_traits:
            parts.append(f"Traits: {', '.join(self.personality_traits)}")
        if self.values:
            parts.append(f"Values: {', '.join(self.values)}")
        if self.fears:
            parts.append(f"Fears: {', '.join(self.fears)}")
        if self.speech_style:
            parts.append(f"Speech style: {self.speech_style}")
        return "; ".join(parts) if parts else ""

    def describe_state(self) -> str:
        """Generate current state description for LLM context."""
        parts = []
        if self.current_mood:
            parts.append(f"Mood: {self.current_mood}")
        if self.current_goal:
            parts.append(f"Goal: {self.current_goal}")
        if self.equipped:
            parts.append(f"Equipped: {', '.join(self.equipped)}")
        return "; ".join(parts) if parts else ""

    def add_item(self, name: str, description: str = "", quantity: int = 1):
        """Add an item to inventory."""
        for item in self.inventory:
            if item["name"] == name:
                item["quantity"] = item.get("quantity", 1) + quantity
                return
        self.inventory.append({"name": name, "description": description, "quantity": quantity})

    def remove_item(self, name: str, quantity: int = 1) -> bool:
        """Remove an item from inventory. Returns False if not enough."""
        for item in self.inventory:
            if item["name"] == name:
                if item.get("quantity", 1) >= quantity:
                    item["quantity"] = item.get("quantity", 1) - quantity
                    if item["quantity"] <= 0:
                        self.inventory.remove(item)
                        if name in self.equipped:
                            self.equipped.remove(name)
                    return True
                return False
        return False


@dataclass
class CharacterAction:
    """A structured action taken by a character (PC or NPC)."""
    character_name: str
    character_id: Optional[int] = None
    action: str = ""          # What they do (physical action)
    speech: str = ""          # What they say (dialogue)
    inner_thought: str = ""   # Internal monologue (optional)
    is_pc: bool = False       # True if this is a playing character

    def to_dict(self) -> dict:
        return {
            "character_name": self.character_name,
            "character_id": self.character_id,
            "action": self.action,
            "speech": self.speech,
            "inner_thought": self.inner_thought,
            "is_pc": self.is_pc
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CharacterAction":
        return cls(
            character_name=data.get("character_name", ""),
            character_id=data.get("character_id"),
            action=data.get("action", ""),
            speech=data.get("speech", ""),
            inner_thought=data.get("inner_thought", ""),
            is_pc=data.get("is_pc", False)
        )

    def to_narrative(self) -> str:
        """Convert to readable narrative text."""
        parts = []
        if self.action:
            parts.append(self.action)
        if self.speech:
            parts.append(f'"{self.speech}"')
        return " ".join(parts) if parts else ""


@dataclass
class Scene:
    """Tracks the current scene state in an adventure."""
    id: Optional[int] = None
    adventure_id: Optional[int] = None
    location_name: str = ""
    location_description: str = ""
    characters_present: list[str] = field(default_factory=list)  # Character names in scene
    situation: str = ""           # What's happening right now
    mood: str = ""                # Atmosphere/tone
    time_of_day: str = ""         # Morning, afternoon, night, etc.
    weather: str = ""             # If relevant
    notes: str = ""               # Additional context
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "adventure_id": self.adventure_id,
            "location_name": self.location_name,
            "location_description": self.location_description,
            "characters_present": self.characters_present,
            "situation": self.situation,
            "mood": self.mood,
            "time_of_day": self.time_of_day,
            "weather": self.weather,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Scene":
        return cls(
            id=data.get("id"),
            adventure_id=data.get("adventure_id"),
            location_name=data.get("location_name", ""),
            location_description=data.get("location_description", ""),
            characters_present=data.get("characters_present", []),
            situation=data.get("situation", ""),
            mood=data.get("mood", ""),
            time_of_day=data.get("time_of_day", ""),
            weather=data.get("weather", ""),
            notes=data.get("notes", "")
        )

    def describe(self) -> str:
        """Generate a scene description for context."""
        parts = []
        if self.location_name:
            parts.append(f"Location: {self.location_name}")
        if self.location_description:
            parts.append(self.location_description)
        if self.time_of_day:
            parts.append(f"Time: {self.time_of_day}")
        if self.weather:
            parts.append(f"Weather: {self.weather}")
        if self.mood:
            parts.append(f"Mood: {self.mood}")
        if self.characters_present:
            parts.append(f"Present: {', '.join(self.characters_present)}")
        if self.situation:
            parts.append(f"Situation: {self.situation}")
        return "\n".join(parts)


@dataclass
class Plot:
    """The plot defines the initial state and context of an adventure."""
    story: str = ""
    ai_instructions: str = ""
    story_summary: str = ""
    plot_essentials: str = ""
    authors_note: str = ""
    third_person: bool = False

    def to_dict(self) -> dict:
        return {
            "story": self.story,
            "ai_instructions": self.ai_instructions,
            "story_summary": self.story_summary,
            "plot_essentials": self.plot_essentials,
            "authors_note": self.authors_note,
            "third_person": self.third_person
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plot":
        return cls(
            story=data.get("story", ""),
            ai_instructions=data.get("ai_instructions", ""),
            story_summary=data.get("story_summary", ""),
            plot_essentials=data.get("plot_essentials", ""),
            authors_note=data.get("authors_note", ""),
            third_person=data.get("third_person", False)
        )


@dataclass
class StoryCard:
    """Story cards provide additional context or trigger events."""
    id: Optional[int] = None
    scenario_id: Optional[int] = None
    type: StoryCardType = StoryCardType.CUSTOM
    name: str = ""
    entry: str = ""  # Content injected into the story
    triggers: list[str] = field(default_factory=list)
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "type": self.type.value if isinstance(self.type, StoryCardType) else self.type,
            "name": self.name,
            "entry": self.entry,
            "triggers": self.triggers,
            "notes": self.notes
        }


@dataclass
class Scenario:
    """Blueprint for an adventure containing all info to start a game."""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    status: ScenarioStatus = ScenarioStatus.DRAFT
    plot: Plot = field(default_factory=Plot)
    story_cards: list[StoryCard] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "status": self.status.value if isinstance(self.status, ScenarioStatus) else self.status,
            "plot": self.plot.to_dict() if isinstance(self.plot, Plot) else self.plot
        }


@dataclass
class Event:
    """An event in the adventure history."""
    id: Optional[int] = None
    adventure_id: Optional[int] = None
    action_type: ActionType = ActionType.DO
    actor_name: str = ""          # Who took the action (PC name or "narrator")
    player_input: str = ""        # Raw input
    narration: str = ""           # Story Director's narration
    character_actions: list[CharacterAction] = field(default_factory=list)  # NPC/PC actions
    scene_update: Optional[dict] = None  # Scene changes from this event
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "adventure_id": self.adventure_id,
            "action_type": self.action_type.value if isinstance(self.action_type, ActionType) else self.action_type,
            "actor_name": self.actor_name,
            "player_input": self.player_input,
            "narration": self.narration,
            "character_actions": [ca.to_dict() for ca in self.character_actions],
            "scene_update": self.scene_update
        }

    @property
    def ai_response(self) -> str:
        """Backward compatibility - combine narration and character actions."""
        parts = []
        if self.narration:
            parts.append(self.narration)
        for ca in self.character_actions:
            if not ca.is_pc:  # Only include NPC actions in AI response
                narrative = ca.to_narrative()
                if narrative:
                    parts.append(f"{ca.character_name}: {narrative}")
        return "\n\n".join(parts)


@dataclass
class Adventure:
    """An instance of a Scenario being played. Stores progress and story."""
    id: Optional[int] = None
    scenario_id: Optional[int] = None
    title: str = ""
    current_story_summary: str = ""
    memory: str = ""  # Active context for LLM
    current_scene: Optional[Scene] = None  # Current scene state
    history: list[Event] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "title": self.title,
            "current_story_summary": self.current_story_summary,
            "memory": self.memory,
            "current_scene": self.current_scene.to_dict() if self.current_scene else None
        }

    def get_pcs_in_scene(self, all_cards: list[StoryCard]) -> list[StoryCard]:
        """Get playing characters currently in the scene."""
        if not self.current_scene:
            return []
        pc_cards = [c for c in all_cards if c.type == StoryCardType.PLAYING_CHARACTER]
        return [c for c in pc_cards if c.name in self.current_scene.characters_present]

    def get_npcs_in_scene(self, all_cards: list[StoryCard]) -> list[StoryCard]:
        """Get NPCs currently in the scene."""
        if not self.current_scene:
            return []
        npc_cards = [c for c in all_cards if c.type == StoryCardType.CHARACTER]
        return [c for c in npc_cards if c.name in self.current_scene.characters_present]
