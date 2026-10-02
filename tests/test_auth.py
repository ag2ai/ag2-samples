import time

import jwt
import pytest
from ag2.testing import TestConfig

from .conftest import sse_events


class NeverCalled(TestConfig):
    def create(self):
        raise AssertionError("the agent must not run for an unauthorised request")


@pytest.fixture
def forged_none_token() -> str:
    return jwt.encode({"sub": "u", "name": "Eve", "exp": int(time.time()) + 60}, None, algorithm="none")


async def test_valid_token_gets_event_stream(make_client, run_input, auth_headers):
    client = make_client(TestConfig("Hello Ada"))

    response = await client.post("/weather", json=run_input(), headers=auth_headers)

    assert response.status_code == 200
    types = [e["type"] for e in sse_events(response)]
    assert types[0] == "RUN_STARTED"
    assert types[-1] == "RUN_FINISHED"


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param(lambda t: {}, id="no-token"),
        pytest.param(lambda t: {"Authorization": "Bearer not-a-jwt"}, id="malformed"),
        pytest.param(lambda t: {"Authorization": f"Token {t()}"}, id="wrong-scheme"),
        pytest.param(lambda t: {"Authorization": f"Bearer {t(expires_in=-60)}"}, id="expired"),
        pytest.param(lambda t: {"Authorization": f"Bearer {t(secret='x' * 40)}"}, id="wrong-signature"),
    ],
)
async def test_invalid_token_is_refused_before_agent_runs(make_client, run_input, make_token, headers):
    client = make_client(NeverCalled())

    response = await client.post("/weather", json=run_input(), headers=headers(make_token))

    assert response.status_code == 401


async def test_token_with_no_algorithm_is_refused(make_client, run_input, forged_none_token):
    client = make_client(NeverCalled())

    response = await client.post(
        "/weather", json=run_input(), headers={"Authorization": f"Bearer {forged_none_token}"}
    )

    assert response.status_code == 401


async def test_unconfigured_secret_admits_nobody(make_client, run_input, auth_headers):
    client = make_client(NeverCalled(), secret=None)

    response = await client.post("/weather", json=run_input(), headers=auth_headers)

    assert response.status_code == 500
