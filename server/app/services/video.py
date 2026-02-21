from datetime import datetime, timedelta, date, time
import httpx
from fastapi import HTTPException
from app.core.config import settings
import urllib.parse

# Use settings from your config for better practice
DAILY_API_KEY = settings.DAILY_API_KEY
DAILY_API_URL = "https://api.daily.co/v1/rooms"
SUBDOMAIN = "medhelp" 

async def create_video_room(appointment_id: str, appointment_date: datetime) -> str:
    """
    Generates a unique, secure Jitsi Meet URL for the virtual consultation.
    Jitsi dynamically creates the room when the first person joins the URL.
    """
    
    # 1. Create a unique room name. 
    # Since your appointment_id is a UUID, this room is impossible to guess.
    # We remove hyphens to make it a clean Jitsi string.
    clean_id = str(appointment_id).replace("-", "")
    room_name = f"MedHelpConsultation{clean_id}"
    
    # 2. URL encode the room name just to be perfectly safe
    safe_room_name = urllib.parse.quote(room_name)
    
    # 3. Construct the Jitsi URL
    # We add a config parameter to force the "Pre-join" screen so users 
    # can check their camera before entering the call.
    jitsi_base_url = "https://meet.jit.si/"
    meeting_link = f"{jitsi_base_url}{safe_room_name}#config.prejoinPageEnabled=true"
    
    return meeting_link