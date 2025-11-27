"""
Lore database models for role-playing/story writing feature.
Based on AI Dungeon-style entities.
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
    CHARACTER = "character"
    LOCATION = "location"
    ITEM = "item"
    CLASS = "class"
    RACE = "race"
    FACTION = "faction"
    CUSTOM = "custom"


class ActionType(str, Enum):
    DO = "do"      # Player performs an action
    SAY = "say"    # Player says something
    STORY = "story"  # Player narrates directly


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
    player_input: str = ""
    ai_response: str = ""
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "adventure_id": self.adventure_id,
            "action_type": self.action_type.value if isinstance(self.action_type, ActionType) else self.action_type,
            "player_input": self.player_input,
            "ai_response": self.ai_response
        }


@dataclass
class Adventure:
    """An instance of a Scenario being played. Stores progress and story."""
    id: Optional[int] = None
    scenario_id: Optional[int] = None
    title: str = ""
    current_story_summary: str = ""
    memory: str = ""  # Active context for LLM
    history: list[Event] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "title": self.title,
            "current_story_summary": self.current_story_summary,
            "memory": self.memory
        }
