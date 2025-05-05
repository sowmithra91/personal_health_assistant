# graph.py
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from utilities.llm_provider import llm
from contextlib import asynccontextmanager


@asynccontextmanager
async def make_graph():
    async with MultiServerMCPClient(
        {
            "restaurant_mcp_server": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            },
            "health_profile_mcp": {
                "url": "http://localhost:8001/sse",
                "transport": "sse",
            }
        }
    ) as client:
        agent = create_react_agent(llm, client.get_tools())
        yield agent
