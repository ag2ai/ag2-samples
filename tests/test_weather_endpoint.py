import json

from ag2.events import ModelMessageChunk, ToolCallEvent
from ag2.testing import TestConfig

from .conftest import ADA, sse_events, tool_results

LONDON = {"latitude": 51.5, "longitude": -0.12}


def call(name: str, **arguments) -> ToolCallEvent:
    return ToolCallEvent(name=name, arguments=json.dumps(arguments))


async def test_malformed_run_input_is_422_not_a_server_error(make_client):
    client = make_client(user=ADA)

    response = await client.post("/weather", json={"nonsense": True})

    assert response.status_code == 422


async def test_capabilities_are_public(make_client):
    client = make_client()

    response = await client.get("/weather")

    assert response.status_code == 200


async def test_agent_resolves_city_then_reports_current_weather(make_client, run_input):
    client = make_client(
        TestConfig(
            call("get_coords_by_city", city="London"),
            call("get_current_weather_by_coords", coords=LONDON),
            "It is overcast in London.",
        ),
        user=ADA,
    )

    response = await client.post("/weather", json=run_input("weather in London"))

    place, weather = tool_results(response)
    assert place["name"] == "London"
    assert weather["location"] == "Current Weather at London, United Kingdom"
    assert weather["conditions"] == "Overcast"


async def test_stream_has_progressive_text_and_brackets_each_tool_call(make_client, run_input):
    client = make_client(
        TestConfig(
            ModelMessageChunk("Looking "),
            ModelMessageChunk("it up."),
            call("get_weather_next_week", coords=LONDON),
            "Rain all week.",
        ),
        user=ADA,
    )

    response = await client.post("/weather", json=run_input("forecast"))

    types = [e["type"] for e in sse_events(response)]
    assert types.count("TEXT_MESSAGE_CONTENT") >= 2
    assert types.index("TOOL_CALL_START") < types.index("TOOL_CALL_END") < types.index("TOOL_CALL_RESULT")
    assert types[-1] == "RUN_FINISHED"
    [forecast] = tool_results(response)
    assert len(forecast["days"]) == 7


async def test_agent_knows_the_user_from_the_token(make_client, run_input, auth_headers):
    client = make_client(TestConfig(call("get_current_user"), "You are Ada"))

    response = await client.post("/weather", json=run_input("who am I?"), headers=auth_headers)

    assert tool_results(response) == [{"id": "user-1", "name": "Ada"}]


async def test_user_claimed_in_state_or_forwarded_props_is_ignored(make_client, run_input):
    forged = {"user": {"id": "evil", "name": "Eve"}, "name": "Eve"}
    client = make_client(TestConfig(call("get_current_user"), "done"), user=ADA)

    response = await client.post(
        "/weather", json=run_input("who am I?", state=forged, forwardedProps=forged)
    )

    assert tool_results(response) == [{"id": "user-1", "name": "Ada"}]


async def test_user_is_not_sent_back_in_state(make_client, run_input):
    client = make_client(TestConfig(call("get_current_user"), "done"), user=ADA)

    response = await client.post("/weather", json=run_input("who am I?"))

    state_frames = [e for e in sse_events(response) if e["type"] in ("STATE_SNAPSHOT", "STATE_DELTA")]
    assert all("Ada" not in json.dumps(e) for e in state_frames)
