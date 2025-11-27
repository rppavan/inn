
# Entities and Schema

This document defines the core entities and their schemas used in the AI Dungeon platform.

## Scenario

A `Scenario` is the blueprint for an adventure. It contains all the information needed to start a new game.

| Attribute | Type | Description |
|---|---|---|
| `title` | String | The title of the scenario. |
| `description` | String | A brief description of the scenario. |
| `tags` | Array of Strings | Keywords that describe the scenario. |
| `status` | Enum | The visibility of the scenario (`DRAFT`, `PUBLISHED`, `UNAVAILABLE`) |
| `plot` | Plot | The plot of the scenario. |
| `storyCards` | Array of Story Cards | A collection of story cards associated with the scenario. |

## Adventure

An `Adventure` is an instance of a `Scenario` being played by a user. It stores the user's progress and the story so far.

| Attribute | Type | Description |
|---|---|---|
| `scenario` | Scenario | The scenario that the adventure is based on. |
| `history` | Array of Events | The history of events that have occurred in the adventure. |
| `state` | Object | The current state of the adventure. |

## Plot

The `Plot` defines the initial state and context of an adventure.

| Attribute | Type | Description |
|---|---|---|
| `story` | String | The initial text that starts the adventure. |
| `aiInstructions` | String | Instructions for the AI to follow. |
| `storySummary` | String | A summary of the story so far. |
| `plotEssentials` | String | Key plot points that the AI should be aware of. |
| `authorsNote` | String | A note from the author to the AI. |
| `thirdPerson` | String | Flag to enable input in third person. |


## Story Card

A `Story Card` provides additional context or triggers events within an adventure.

| Attribute | Type | Description |
|---|---|---|
| `type` | Enum | The type of story card (`CHARACTER`, `LOCATION`, `ITEM`, `CLASS`, `RACE`, `FACTION`, `CUSTOM`). |
| `name` | String | The name of the story card. |
| `entry` | String | The content of the story card that is injected into the story. |
| `triggers` | Array of Strings | Keywords that trigger the story card. |
| `notes` | String | Additional notes for the story card. |

## Character

A `Character` is a type of `Story Card` that represents a character in the story.

| Attribute | Type | Description |
|---|---|---|
| `name` | String | The name of the character. |
| `description` | String | A description of the character. |

## Location

A `Location` is a type of `Story Card` that represents a location in the story.

| Attribute | Type | Description |
|---|---|---|
| `name` | String | The name of the location. |
| `description` | String | A description of the location.
