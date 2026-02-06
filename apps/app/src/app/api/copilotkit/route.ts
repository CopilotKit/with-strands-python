import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  LangGraphAgent,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";
import { aguiMiddleware } from "@/app/api/copilotkit/ag-ui-middleware";

// 1. Define the agent connection to LangGraph
const defaultAgent = new HttpAgent({
  url: process.env.AGENT_DEPLOYMENT_URL || "http://localhost:8000",
});

// 2. Bind in middleware to the agent. For A2UI and MCP Apps.
defaultAgent.use(...aguiMiddleware)

// 3. Define the route and CopilotRuntime for the agent
export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    endpoint: "/api/copilotkit",
    serviceAdapter: new ExperimentalEmptyAdapter(),
    runtime: new CopilotRuntime({
      agents: {
        default: defaultAgent,
      },
    }),
  });

  return handleRequest(req);
};
