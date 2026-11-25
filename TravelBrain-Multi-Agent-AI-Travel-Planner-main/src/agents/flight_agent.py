"""Turns the user query into concrete flight guidance using AviationStack MCP."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agents.prompts import FLIGHT_AGENT_PROMPT, FLIGHT_SYSTEM_PROMPT
from src.clients.llm import invoke_llm
from src.config.settings import (
    AIRLINE_DATA_CHAR_LIMIT,
    AIRPORT_DATA_CHAR_LIMIT,
)
from src.graph.state import TravelState
from src.mcp_servers.local import aviation_mcp_call
from src.utils.async_utils import bump_llm_calls, run_async, truncate


def flight_agent(state: TravelState):
    print("\nINSIDE FLIGHT AGENT\n")

    query = state["user_query"]

    airports = run_async(aviation_mcp_call("list_airports"))
    airlines = run_async(aviation_mcp_call("list_airlines"))

    print("\nAIRPORTS:", airports)
    print("\nAIRLINES:", airlines)

    prompt = FLIGHT_AGENT_PROMPT.format(
        query=query,
        airport_data=truncate(airports, AIRPORT_DATA_CHAR_LIMIT),
        airline_data=truncate(airlines, AIRLINE_DATA_CHAR_LIMIT),
    )

    response = invoke_llm([
        SystemMessage(content=FLIGHT_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ], max_tokens=700)

    flight_data = response.content

    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(content="Flight recommendations generated")
        ],
        "llm_calls": bump_llm_calls(state),
    }
