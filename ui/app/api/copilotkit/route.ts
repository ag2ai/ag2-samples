import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";
import {
  CopilotRuntime,
  createCopilotRuntimeHandler,
} from "@copilotkit/runtime/v2";

export const POST = async (req: NextRequest) => {
  // The agent is built per request so the caller's Access token is forwarded to the
  // backend, which is the one that decides whether it is valid.
  const runtime = new CopilotRuntime({
    agents: {
      agenticChatAgent: new HttpAgent({
        url: `http://localhost:8000/weather`,
        headers: { Authorization: req.headers.get("authorization") ?? "" },
      }),
    },
  });

  return createCopilotRuntimeHandler({
    runtime,
    basePath: "/api/copilotkit",
    mode: "single-route",
  })(req);
};
