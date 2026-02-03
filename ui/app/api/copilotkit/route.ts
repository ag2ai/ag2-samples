import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";
import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
  ExperimentalEmptyAdapter,
} from "@copilotkit/runtime";

const serviceAdapter = new ExperimentalEmptyAdapter();


const agenticChatAgent = new HttpAgent({
  url: `http://localhost:8000/weather/`,
});

const runtime = new CopilotRuntime({
  agents: {
    agenticChatAgent,
  },
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
