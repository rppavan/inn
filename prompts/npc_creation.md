# NPC Creation Prompt Template

This template is used when the story director needs to create a new character on the fly.

## System Context

You are creating a new character for an interactive story. The character should fit naturally into the world and current situation.

## World Context

### Setting
```
{scenario_description}
```

### Current Story Context
```
{story_summary}
```

### Existing Characters
```
{existing_characters}
```

## Creation Request

Create a new character based on this context: {creation_context}

## Output Format

Provide the character in the following format:

**Name**: [Character name]

**Type**: [CHARACTER]

**Entry**: [A 2-3 sentence description that can be injected into the story when this character appears. Write in third person present tense.]

**Triggers**: [Comma-separated list of keywords that should trigger this character's inclusion in the story]

**Notes**: [Additional details for the story director: personality traits, motivations, secrets, relationships, etc.]

## Guidelines

- Create memorable, distinct characters
- Give them clear motivations and personality traits
- Consider their role in the story (ally, antagonist, neutral, comic relief, etc.)
- Include at least one interesting quirk or detail
- Make triggers specific enough to avoid false positives
