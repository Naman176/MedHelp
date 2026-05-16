import json
import os
from mcp.server.fastmcp import FastMCP
from app.chatbot.services.doctor_service import ( list_available_specializations, search_available_doctors )

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))

mcp = FastMCP(
    "MedHelp MCP",
    port=PORT,
    host=HOST,
)


@mcp.tool()
async def ping() -> str:
    return "pong"


@mcp.tool()
async def list_specializations() -> str:
    result = await list_available_specializations()
    return json.dumps(result)


@mcp.tool()
async def get_available_doctors(specialist_type: str, days: list[str]) -> str:
    result = await search_available_doctors(specialist_type, days)
    return json.dumps(result)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")