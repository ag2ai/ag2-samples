"""The AG-UI endpoint that serves the weather agent."""

from typing import Annotated

from ag2.ag_ui import AGUIStream
from ag2.config import ModelConfig
import httpx2
from ag_ui.core import RunAgentInput
from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse, StreamingResponse

from ..auth import authorised_user
from ..models import User


def create_router(
    stream: AGUIStream, http: httpx2.AsyncClient, config: ModelConfig | None = None
) -> APIRouter:
    """Build the weather router. `config` replaces the agent's model, for tests."""
    router = APIRouter()

    @router.get("/weather")
    async def capabilities() -> JSONResponse:
        return JSONResponse(stream.capabilities().model_dump(by_alias=True, exclude_none=True))

    # The stock `stream.build_asgi()` endpoint discards request headers, so the route is
    # written out here to put the User and the HTTP client, and nothing else, into the
    # agent's dependencies.
    @router.post("/weather")
    async def run(
        run_input: RunAgentInput,
        user: Annotated[User, Depends(authorised_user)],
        accept: Annotated[str | None, Header()] = None,
    ) -> StreamingResponse:
        events = stream.dispatch(
            run_input, dependencies={"user": user, "http": http}, config=config, accept=accept
        )
        return StreamingResponse(events)

    return router
