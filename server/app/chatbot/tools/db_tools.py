from langchain_core.tools import tool
import json
from app.chatbot.services.doctor_service import ( list_available_specializations, search_available_doctors,)


@tool
async def get_available_doctors(specialist_type: str, days: list[str]) -> str:
    """
    Query the database for doctors of a given specialization who are available
    on one or more days of the week.

    Args:
        specialist_type: The medical specialization to search for.
                        Use lowercase (e.g. 'cardiologist', 'dentist', 'dermatologist').
                        Partial matches work — 'cardio' matches 'Cardiologist'.

        days: List of day names to check availability for.
              Always pass actual day names — Monday, Tuesday, Wednesday, etc.
              Resolve any relative expressions yourself before calling this tool:
                - "tomorrow"         → figure out the actual day name and pass it
                - "all weekdays"     → ["Monday","Tuesday","Wednesday","Thursday","Friday"]
                - "tuesday and thursday" → ["Tuesday", "Thursday"]
                - "all week"         → ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
                - "all except sunday"→ ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
                - "weekend"          → ["Saturday", "Sunday"]

    Returns:
        JSON string. Each doctor entry contains name, specialization,
        experience, consultation fee, bio, and slots grouped by day.
    """
    
    result = await search_available_doctors(specialist_type, days)
    return json.dumps(result)


@tool
async def list_specializations() -> str:
    """
    Get all unique doctor specializations currently available in the system.

    Use this when:
    - The user is unsure what type of doctor they need
    - The user asks "what doctors do you have?" or "what specialties are available?"
    - No specialist has been recommended yet and the user's message is unclear

    Returns:
        JSON string with a list of all available specialization names.
    """
    result = await list_available_specializations()
    return json.dumps(result)