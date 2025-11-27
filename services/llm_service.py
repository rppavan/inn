from litellm import completion
from state import settings

async def get_chat_completion(message: str) -> str:
    """
    Get a chat completion from the configured LLM model.

    Args:
        message: User message to send to the LLM

    Returns:
        The AI's response content

    Raises:
        Exception: If the LLM API call fails
    """
    kwargs = {
        "model": settings["model"],
        "messages": [{"role": "user", "content": message}]
    }

    if settings["api_base"]:
        kwargs["api_base"] = settings["api_base"]
        kwargs["custom_llm_provider"] = "openai"
        kwargs["api_key"] = "dummy"

    response = completion(**kwargs)
    return response.choices[0].message.content

def update_settings(model: str, api_base: str | None = None) -> dict:
    """
    Update the application settings.

    Args:
        model: The LLM model identifier
        api_base: Optional API base URL

    Returns:
        The updated settings dictionary
    """
    settings["model"] = model
    settings["api_base"] = api_base if api_base else ""
    return settings
