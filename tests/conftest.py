import json
import time
from collections.abc import AsyncIterator, Callable
from contextlib import AsyncExitStack

import httpx2
import jwt
import pytest
from ag2.config import ModelConfig
from ag2.testing import TestConfig
from fastapi import FastAPI

from backend.app import create_app
from backend.auth import authorised_user
from backend.models import User

from . import open_meteo_payloads as payloads

SECRET = "test-secret-with-enough-length-for-hs256"
ADA = User(id="user-1", name="Ada")


@pytest.fixture
def auth_secret() -> str:
    return SECRET


@pytest.fixture
def open_meteo_upstream() -> httpx2.AsyncClient:
    """A client answering with canned Open-Meteo responses instead of the network."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        if "geocoding" in request.url.host:
            return httpx2.Response(200, json=payloads.GEOCODING)
        if "daily" in request.url.params:
            return httpx2.Response(200, json=payloads.DAILY)
        return httpx2.Response(200, json=payloads.CURRENT)

    return httpx2.AsyncClient(transport=httpx2.MockTransport(handler))


@pytest.fixture
def make_token(auth_secret: str) -> Callable[..., str]:
    def make(*, secret: str | None = None, expires_in: int = 3600, name: str = "Ada") -> str:
        claims = {"sub": "user-1", "name": name, "exp": int(time.time()) + expires_in}
        return jwt.encode(claims, secret or auth_secret, algorithm="HS256")

    return make


@pytest.fixture
def auth_headers(make_token: Callable[..., str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token()}"}


@pytest.fixture
async def make_client(
    auth_secret: str, open_meteo_upstream: httpx2.AsyncClient
) -> AsyncIterator[Callable[..., httpx2.AsyncClient]]:
    """Build a client for the app running `model`. Pass `user` to skip token checks, `secret=None` to leave auth unconfigured."""
    async with AsyncExitStack() as stack:

        def make(
            model: ModelConfig | None = None,
            *,
            user: User | None = None,
            secret: str | None = auth_secret,
        ) -> httpx2.AsyncClient:
            app: FastAPI = create_app(
                model or TestConfig("ok"), http=open_meteo_upstream, auth_secret=secret
            )
            if user is not None:
                app.dependency_overrides[authorised_user] = lambda: user
            transport = httpx2.ASGITransport(app=app, raise_app_exceptions=False)
            client = httpx2.AsyncClient(transport=transport, base_url="http://test")
            stack.push_async_callback(client.aclose)
            return client

        yield make


@pytest.fixture
def run_input() -> Callable[..., dict]:
    def make(text: str = "hi", **extra) -> dict:
        return {
            "threadId": "t1",
            "runId": "r1",
            "messages": [{"id": "m1", "role": "user", "content": text}],
            "state": {},
            "context": [],
            "tools": [],
            "forwardedProps": {},
        } | extra

    return make


def sse_events(response: httpx2.Response) -> list[dict]:
    return [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]


def tool_results(response: httpx2.Response) -> list[dict]:
    return [json.loads(e["content"]) for e in sse_events(response) if e["type"] == "TOOL_CALL_RESULT"]
