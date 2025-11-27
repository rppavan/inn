# Story Summary Update Prompt Template

This template is used to periodically update the story summary to maintain context without exceeding token limits.

## System Context

You are a narrative analyst tasked with maintaining a concise but comprehensive summary of an ongoing story.

## Current Summary
```
{current_summary}
```

## New Events to Incorporate

{new_events}

## Your Task

Update the story summary to incorporate the new events while:

1. **Preserving Key Information**:
   - Major plot points and revelations
   - Important character introductions and developments
   - Significant locations visited
   - Key items acquired or lost
   - Relationship changes

2. **Maintaining Brevity**:
   - Keep the summary under 500 words
   - Focus on information relevant to future story progression
   - Remove outdated or superseded information
   - Combine related events into concise statements

3. **Tracking Open Threads**:
   - Note unresolved plot points
   - Track ongoing character arcs
   - Remember promises made or quests accepted

## Output Format

Provide the updated summary as flowing prose, organized chronologically or by theme as appropriate. Do not include headers or bullet points in the final summary.
