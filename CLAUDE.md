# CopilotKit + AWS Strands Starter

## Purpose

This repository serves as both a **showcase** and **template** for building AI agents with CopilotKit and AWS Strands. It demonstrates how CopilotKit can drive interactive UI beyond just chat, using an **agent-driven application** as the primary example.

**Target audience:** Developers evaluating CopilotKit or starting new projects with AI agents using AWS Strands.

## Core Concept

This starter demonstrates **agent-driven UI** where:
- The agent can manipulate application state through backend tools
- Users can interact with the same state through the frontend UI
- Both agent and user changes update the same shared state
- The UI reactively updates based on agent state changes

This uses CopilotKit's **v2 agent state pattern** integrated with AWS Strands, where state lives in the agent and syncs bidirectionally to the frontend.

## Architecture

This is a **monorepo** with multiple apps:

### Repository Structure

```
apps/
├── app/                         # Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # Main page - wires up all components
│   │   │   └── api/copilotkit/ # CopilotKit API route
│   │   ├── components/
│   │   │   ├── canvas/         # Application UI
│   │   │   │   └── index.tsx   # Canvas container
│   │   │   ├── example-layout/ # Layout: chat + canvas side-by-side
│   │   │   └── generative-ui/  # Example generative UI components
│   │   └── hooks/
│   │       ├── use-generative-ui-examples.tsx  # Example CopilotKit patterns
│   │       └── use-example-suggestions.tsx     # Chat suggestions
└── agent/                       # AWS Strands Python agent
    ├── main.py                  # Agent entry point
    └── pyproject.toml           # Python dependencies
```

## Key Pattern: Agent State with CopilotKit v2 + AWS Strands

This starter uses **CopilotKit v2's agent state pattern** integrated with **AWS Strands** where state lives in the agent backend and syncs bidirectionally with the frontend.

### How It Works

1. **Agent defines tools with Strands** (Python)
   ```python
   # apps/agent/main.py
   from strands import Agent, tool
   from strands.models.openai import OpenAIModel
   from ag_ui_strands import StrandsAgent, StrandsAgentConfig, create_strands_app

   @tool
   def update_proverbs(proverbs_list: ProverbsList):
       """Update the complete list of proverbs.

       Args:
           proverbs_list: The complete updated proverbs list

       Returns:
           Success message
       """
       return "Proverbs updated successfully"

   # Create Strands agent
   strands_agent = Agent(
       model=OpenAIModel(model_id="gpt-4o"),
       system_prompt="You are a helpful assistant...",
       tools=[update_proverbs, get_weather],
   )

   # Wrap with AG-UI integration for CopilotKit
   agui_agent = StrandsAgent(
       agent=strands_agent,
       name="proverbs_agent",
       description="A proverbs assistant",
       config=shared_state_config,
   )
   ```

2. **Frontend reads from agent state**
   ```typescript
   // apps/app/src/components/canvas/index.tsx
   const { agent } = useAgent();

   return (
     <Canvas
       data={agent.state?.proverbs || []}
       onUpdate={(updatedData) => agent.setState({ proverbs: updatedData })}
       isAgentRunning={agent.isRunning}
     />
   );
   ```

3. **User interactions update agent state**
   ```typescript
   // User makes changes → frontend calls agent.setState()
   const updateData = (newData) => {
     agent.setState({ proverbs: newData });
   };
   ```

4. **Agent can manipulate state via tools**
   - The agent calls tools (e.g., `update_proverbs`) to modify application state
   - Both user and agent changes update the same `agent.state`
   - Frontend automatically re-renders when state changes
   - State flows through AG-UI integration layer

### Why This Pattern?

- **Single source of truth**: State lives in the agent, not duplicated in frontend
- **Bidirectional sync**: User changes → agent state, Agent changes → UI update
- **Simple**: No need for separate frontend state management
- **Observable**: Agent has full visibility into state changes

## Implementation Details

### Agent Backend

**Agent Definition** (`apps/agent/main.py`):
```python
from strands import Agent, tool
from strands.models.openai import OpenAIModel
from ag_ui_strands import (
    StrandsAgent,
    StrandsAgentConfig,
    ToolBehavior,
    create_strands_app,
)

# Initialize OpenAI model
model = OpenAIModel(
    client_args={"api_key": os.getenv("OPENAI_API_KEY")},
    model_id="gpt-4o",
)

# Create Strands agent with tools
strands_agent = Agent(
    model=model,
    system_prompt="You are a helpful assistant...",
    tools=[update_proverbs, get_weather],
)

# Wrap with AG-UI integration for CopilotKit
agui_agent = StrandsAgent(
    agent=strands_agent,
    name="proverbs_agent",
    description="A proverbs assistant",
    config=shared_state_config,
)

# Create FastAPI app
app = create_strands_app(agui_agent, agent_path="/")
```

**Tool Definition Example**:
```python
from pydantic import BaseModel, Field

class ProverbsList(BaseModel):
    """A list of proverbs."""
    proverbs: List[str] = Field(description="The complete list of proverbs")

@tool
def update_proverbs(proverbs_list: ProverbsList):
    """Update the complete list of proverbs.

    Args:
        proverbs_list: The complete updated proverbs list

    Returns:
        Success message
    """
    return "Proverbs updated successfully"

@tool
def get_weather(location: str):
    """Get the weather for a location.

    Args:
        location: The location to get weather for

    Returns:
        Weather information
    """
    return json.dumps({"location": location, "temp": "70 degrees"})
```

**State Management Configuration**:
```python
async def proverbs_state_from_args(context):
    """Extract proverbs state from tool arguments."""
    tool_input = context.tool_input
    if isinstance(tool_input, str):
        tool_input = json.loads(tool_input)

    proverbs_data = tool_input.get("proverbs_list", tool_input)
    proverbs_array = proverbs_data.get("proverbs", [])

    return {"proverbs": proverbs_array}

# Configure state management
shared_state_config = StrandsAgentConfig(
    state_context_builder=build_proverbs_prompt,
    tool_behaviors={
        "update_proverbs": ToolBehavior(
            skip_messages_snapshot=True,
            state_from_args=proverbs_state_from_args,
        )
    },
)
```

### Frontend

**Main Page** (`apps/app/src/app/page.tsx`):
```typescript
"use client";

import { ExampleLayout } from "@/components/example-layout";
import { Canvas } from "@/components/canvas";
import { useGenerativeUIExamples, useExampleSuggestions } from "@/hooks";
import { CopilotChat } from "@copilotkit/react-core/v2";

export default function HomePage() {
  // Generative UI Examples
  useGenerativeUIExamples();

  // Example Suggestions
  useExampleSuggestions();

  return (
    <ExampleLayout
      chatContent={<CopilotChat key="chat" />}
      appContent={<Canvas />}
    />
  );
}
```

**Canvas Component** (`apps/app/src/components/canvas/index.tsx`):
```typescript
export function Canvas() {
  const { agent } = useAgent();  // CopilotKit v2 hook

  return (
    <div className="h-full p-8 bg-gray-50">
      {/* Your application UI goes here */}
      {/* Read state from agent.state */}
      {/* Update state via agent.setState() */}
      <YourComponent
        data={agent.state?.yourData || []}
        onUpdate={(newData) => agent.setState({ yourData: newData })}
        isAgentRunning={agent.isRunning}
      />
    </div>
  );
}
```

### How State Flows

1. **User interacts with UI** → Frontend calls `agent.setState({ yourData: [...] })`
2. **Agent state updates** → CopilotKit syncs to backend via AG-UI protocol
3. **Strands agent observes change** → Can respond via tools based on state context
4. **Agent modifies state** → Calls tools which emit state updates via `state_from_args`
5. **State syncs to frontend** → `agent.state` updates through AG-UI integration
6. **UI re-renders** → React sees new state and updates display

**Key insight**: State lives in the Strands agent backend, frontend just reads/writes to it via CopilotKit hooks. The AG-UI integration layer handles the bidirectional sync.

## Tech Stack

- **Frontend**: Next.js, React, TailwindCSS
- **Agent**: AWS Strands (Python), OpenAI GPT-4o
- **Integration**: ag-ui-strands for CopilotKit v2 integration
- **CopilotKit**: React hooks for agent state management (v2)
- **Package Manager**: pnpm (recommended), npm, yarn, or bun
- **Server**: FastAPI + Uvicorn
- **Python**: Python 3.12+ with uv for dependency management

## Development

This is a monorepo with support for multiple package managers (pnpm, npm, yarn, bun).

### Installation

```bash
# Using pnpm (recommended)
pnpm install

# Using npm
npm install

# Using yarn
yarn install

# Using bun
bun install
```

> **Note:** Installing dependencies will automatically install the agent's Python dependencies via the `install:agent` script.

### Available Scripts

```bash
# Start both UI and agent in development mode
pnpm dev        # or npm run dev, yarn dev, bun run dev

# Start with debug logging
pnpm dev:debug

# Start individually
pnpm dev:ui     # Next.js frontend only
pnpm dev:agent  # Strands agent only (port 8000)

# Build for production
pnpm build

# Start production server
pnpm start

# Lint
pnpm lint

# Install Python dependencies manually
pnpm install:agent
```

### Environment Setup

```bash
# Set OpenAI API key for the Strands agent
export OPENAI_API_KEY="your-openai-api-key-here"

# Or create a .env file in the agent directory
echo "OPENAI_API_KEY=your-openai-api-key-here" > apps/agent/.env
```

### Configuration

The agent server can be configured via environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `AGENT_PORT` - Agent server port (default: 8000)
- `AGENT_PATH` - Agent endpoint path (default: /)

## Design Principles

1. **Simple over complex** - The starter is intentionally focused and minimal
2. **CopilotKit v2 patterns** - Uses modern agent state management
3. **AWS Strands integration** - Leverages Strands for agent orchestration
4. **Template-first** - Code is meant to be forked and extended
5. **Showcasing agent-driven UI** - Demonstrates AI manipulating application state beyond chat

## Key Features

- **Shared State Management**: Bidirectional sync between agent and UI
- **Backend Tools**: Execute tools in the Strands agent backend
- **Generative UI**: Examples of rendering dynamic UI from agent responses
- **OpenAI Integration**: Uses OpenAI models via Strands
- **FastAPI Server**: Production-ready agent server with hot reloading
- **TypeScript Frontend**: Type-safe React components with CopilotKit

---

## Key Takeaways for Developers

**State Management Pattern**: This starter uses CopilotKit v2's agent state pattern with AWS Strands:

### Backend (Strands Agent)
1. **Define tools with Pydantic models**:
   ```python
   @tool
   def your_tool(data: YourModel):
       """Tool description"""
       return "Success"
   ```

2. **Configure state extraction**:
   ```python
   async def state_from_args(context):
       """Extract state from tool arguments"""
       return {"yourData": extracted_data}

   config = StrandsAgentConfig(
       tool_behaviors={
           "your_tool": ToolBehavior(state_from_args=state_from_args)
       }
   )
   ```

3. **Wrap agent with AG-UI integration**:
   ```python
   agui_agent = StrandsAgent(
       agent=strands_agent,
       name="your_agent",
       config=config,
   )
   ```

### Frontend (React/Next.js)
1. **Read state**: `agent.state?.yourData`
2. **Write state**: `agent.setState({ yourData: newData })`
3. **React to changes**: `agent.isRunning`

### Why This Pattern?

- **Single source of truth**: State lives in the Strands agent backend
- **Bidirectional sync**: User changes → agent state, Agent changes → UI update
- **No manual state management**: AG-UI handles synchronization
- **Type-safe**: Pydantic models ensure data validation
- **Observable**: Agent has full visibility into state changes

This pattern works great for **agent-driven applications** where AI needs to manipulate structured application state beyond just chat responses.

## Extending This Template

1. **Add new tools** in `apps/agent/main.py` using the `@tool` decorator
2. **Configure state extraction** via `state_from_args` callbacks
3. **Update frontend** to read/write new state fields via `agent.state` and `agent.setState()`
4. **Customize UI** in `apps/app/src/components/` to match your application needs

## Troubleshooting

### Agent Connection Issues
If you see connection errors:
1. Ensure the Strands agent is running on port 8000
2. Verify your OpenAI API key is set correctly
3. Check that both frontend and agent servers started successfully

### Python Dependencies
If you encounter import errors:
```bash
cd apps/agent
uv sync
```
