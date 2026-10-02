"""The weather agent: its prompt, model and tools."""

from textwrap import dedent

from ag2 import Agent
from ag2.config import OpenAIResponsesConfig

from .tools import (
    get_coords_by_city,
    get_current_user,
    get_current_weather_by_coords,
    get_weather_next_week,
    save_favorite_city,
)

PROMPT = dedent("""
    You are a helpful weather assistant. Answer weather questions with the available
    tools; each tool's own description says when it applies.

    A weather tool needs coordinates, so resolve the place first.
    - For "weather here", "my location", "where I am", or similar: call the
      getUserLocation frontend tool, then pass the coordinates it returns to the
      weather tool the question calls for.
    - If getUserLocation fails (e.g. permission denied or location unavailable): ask
      the user for their city name ("I couldn't get your location. Which city would
      you like the weather for?").
    - For a city name: resolve it with get_coords_by_city, passing a country code when
      the name is ambiguous.

    Always be clear about which city you're reporting on — get_coords_by_city tells you
    which one it matched, and it is not always the one you asked for. If a request is
    unclear, ask for clarification.

    Delegate to sub-agents when the question calls for it:
    - task_ClothingAdvisor: what to wear. Fetch the weather first and pass it as context.
    - task_TripPlanner: comparing the weather in several cities, or picking where to go.
    Use save_favorite_city only when the user asks to save a city; they confirm it first.

    After calling a tool, reply with a single paragraph summarising the result, not a
    list of items. The UI renders the tool result as a card, so keep your text answer a
    concise, informative summary.""")

CONFIG = OpenAIResponsesConfig(
    model="gpt-5.6-sol",
    streaming=True,
)

clothing_advisor = Agent(
    "ClothingAdvisor",
    prompt=(
        "You advise what to wear for given weather. Reply with two or three short, "
        "concrete suggestions (layers, footwear, accessories) based only on the weather you are given."
    ),
    config=CONFIG,
)

trip_planner = Agent(
    "TripPlanner",
    prompt=(
        "You compare the weather of several cities and recommend where to go. Look up "
        "each city with your tools, then answer in one short paragraph naming the best pick and why."
    ),
    config=CONFIG,
    tools=[get_coords_by_city, get_weather_next_week],
)

agent = Agent(
    "WeatherAgent",
    prompt=PROMPT,
    config=CONFIG,
    tools=[
        get_coords_by_city,
        get_current_weather_by_coords,
        get_weather_next_week,
        get_current_user,
        save_favorite_city,
        clothing_advisor.as_tool(
            description="Suggest what to wear for the given weather. Pass the weather summary as context."
        ),
        trip_planner.as_tool(
            description="Compare the weather of several cities and recommend where to go."
        ),
    ],
)
