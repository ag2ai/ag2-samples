"""The FastAPI app that serves the agent over AG-UI."""

import os

import httpx2
from ag2.ag_ui import AGUIStream
from ag2.config import ModelConfig
from fastapi import FastAPI

from . import openmeteo
from .agent import agent
from .auth import AUTH_SECRET_ENV
from .routers import weather


def create_app(
    config: ModelConfig | None = None,
    *,
    http: httpx2.AsyncClient | None = None,
    auth_secret: str | None = None,
) -> FastAPI:
    """Build the backend. The arguments replace what the app would otherwise reach out for:
    `config` the agent's model, `http` the Open-Meteo client, `auth_secret` the key Access
    tokens are verified with (none: every request is refused). Meant for tests."""
    app = FastAPI()
    app.state.auth_secret = auth_secret
    app.include_router(weather.create_router(AGUIStream(agent), http or openmeteo.new_client(), config))
    return app


app = create_app(auth_secret=os.environ.get(AUTH_SECRET_ENV))
