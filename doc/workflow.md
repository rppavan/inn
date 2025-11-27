
# Workflow

This document describes the workflow for creating and playing through an adventure on the AI Dungeon platform.

## 1. Scenario Creation

The process of creating a new adventure starts with creating a `Scenario`. This is done through the following steps:

1.  **Navigate to the "New Scenario" page:** The user initiates the scenario creation process by navigating to the "New Scenario" page.
2.  **Choose a template:** The user can choose from a variety of templates to pre-populate the scenario with content.
3.  **Fill in the scenario details:** The user provides the following information:
    *   **Title:** A title for the scenario.
    *   **Description:** A description of the scenario.
    *   **Tags:** Keywords to help users find the scenario.
4.  **Define the plot:** The user defines the initial state of the adventure by providing a prompt and memory.
5.  **Add story cards:** The user can add `Story Cards` to provide additional context and trigger events within the adventure.
6.  **Add scripting:** The user can add custom logic to the scenario using scripts.
7.  **Save the scenario:** The user saves the scenario, making it available for play.

## 2. Adventure Play-through

Once a `Scenario` is created, users can play through it in an `Adventure`.

1.  **Start a new adventure:** The user starts a new adventure by selecting a scenario.
2.  **The AI generates the initial story:** The AI uses the `Plot` from the scenario to generate the initial story.
3.  **The user interacts with the story:** The user can interact with the story by performing actions, saying things, or telling the story directly.
4.  **The AI responds:** The AI responds to the user's input, generating the next part of the story.
5.  **Story cards are triggered:** As the story progresses, `Story Cards` may be triggered by keywords in the story, injecting additional content.
6.  **The adventure continues:** The adventure continues with the user and the AI taking turns to build the story.

