"""Strands AG-UI Integration Example - Proverbs Agent.

This example demonstrates a Strands agent integrated with AG-UI, featuring:
- Shared state management between agent and UI
- Backend tool execution (get_weather, update_proverbs)
- Frontend tools (set_theme_color)
- Generative UI rendering
"""

import json
import os

from ag_ui_strands import (
    StrandsAgent,
    create_strands_app,
)
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models.openai import OpenAIModel

load_dotenv()

@tool
def get_weather(location: str):
    """Get the weather for a location.

    Args:
        location: The location to get weather for

    Returns:
        Weather information as JSON string
    """
    return json.dumps({"location": "70 degrees"})


api_key = os.getenv("OPENAI_API_KEY", "")
model = OpenAIModel(
    client_args={"api_key": api_key},
    model_id="gpt-5.2",
)

strands_agent = Agent(
    model=model,
    tools=[get_weather],
    system_prompt="""  
       You are a helpful assistant that helps users understand CopilotKit and LangGraph used together.

        When asked about generative UI:
        1. Ground yourself in relevant information from the CopilotKit documentation.
        2. Use one of the relevant tools to demonstrate that piece of generative UI.
        3. Explain the concept to the user with a brief summary.",
    """,
)

# Wrap with AG-UI integration
agui_agent = StrandsAgent(
    agent=strands_agent,
    name="proverbs_agent",
)

# Create the FastAPI app
agent_path = os.getenv("AGENT_PATH", "/")
app = create_strands_app(agui_agent, agent_path)

if __name__ == "__main__":
    import uvicorn

    port  = int(os.getenv("AGENT_PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
