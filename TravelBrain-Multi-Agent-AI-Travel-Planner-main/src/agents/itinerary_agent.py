"""Combines flight, hotel and weather results into a day-by-day itinerary."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agents.prompts import ITINERARY_AGENT_PROMPT, ITINERARY_SYSTEM_PROMPT
from src.clients.llm import invoke_llm
from src.graph.state import TravelState
from src.utils.async_utils import bump_llm_calls, truncate


def itinerary_agent(state: TravelState):
    prompt = ITINERARY_AGENT_PROMPT.format(
        user_query=state["user_query"],
        flight_results=truncate(state["flight_results"], 1800),
        hotel_results=truncate(state["hotel_results"], 3000),
        weather_results=truncate(state["weather_results"], 1800),
    )

    response = invoke_llm([
        SystemMessage(content=ITINERARY_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ], max_tokens=1400)

    return {
        "itinerary": response.content,
        # The full itinerary is already in its dedicated state field and is
        # consumed by final_agent. Keep only a compact checkpoint message.
        "messages": [AIMessage(content="Travel itinerary drafted")],
        "llm_calls": bump_llm_calls(state),
    }
