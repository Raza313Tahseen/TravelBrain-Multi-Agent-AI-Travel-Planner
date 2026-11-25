"""Formats everything the other agents produced into the user-facing answer."""

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.prompts import FINAL_AGENT_PROMPT, FINAL_SYSTEM_PROMPT
from src.clients.llm import invoke_llm
from src.graph.state import TravelState
from src.utils.async_utils import bump_llm_calls, truncate


def final_agent(state: TravelState):
    prompt = FINAL_AGENT_PROMPT.format(
        user_query=state["user_query"],
        flight_results=truncate(state["flight_results"], 900),
        hotel_results=truncate(state["hotel_results"], 1400),
        weather_results=truncate(state["weather_results"], 900),
        itinerary=truncate(state["itinerary"], 5000),
    )

    response = invoke_llm([
        SystemMessage(content=FINAL_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ], max_tokens=1800)

    return {
        "messages": [response],
        "llm_calls": bump_llm_calls(state),
    }
