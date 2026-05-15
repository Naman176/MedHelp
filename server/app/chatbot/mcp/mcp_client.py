"""
mcp_client.py

MCP client that connects to the MedHelp MCP server over HTTP.
Used by the booking_node in graph.py to load tools from the MCP server
instead of importing Python functions directly.

Architecture:
    booking_node
        → MultiServerMCPClient (this file)
        → MCP Server (port 8001)
        → doctor_service.py
        → PostgreSQL

The MCP server must be running before the chatbot can use MCP tools.
If the MCP server is not running, booking_node falls back to direct tools.
"""

from langchain_mcp_adapters.client import MultiServerMCPClient

# MCP server URL — must match host/port/path in mcp_server.py
MCP_SERVER_URL = "http://127.0.0.1:8001/mcp"

# MCP server name — used as identifier in MultiServerMCPClient
MCP_SERVER_NAME = "medhelp"


def get_mcp_client() -> MultiServerMCPClient:
    """
    Creates and returns a MultiServerMCPClient pointed at the MedHelp MCP server.

    MultiServerMCPClient is the LangChain adapter that:
    1. Connects to your MCP server over HTTP
    2. Fetches the list of available tools (get_available_doctors, list_specializations, etc.)
    3. Converts them into LangChain-compatible tool objects
    4. Lets you bind them to an LLM exactly like regular @tool functions

    Usage in booking_node:
        client = get_mcp_client()
        async with client:
            tools = await client.get_tools()
            llm_with_mcp_tools = llm.bind_tools(tools)
    """
    return MultiServerMCPClient(
        {
            MCP_SERVER_NAME: {
                "transport": "streamable_http",
                "url": MCP_SERVER_URL,
            }
        }
    )