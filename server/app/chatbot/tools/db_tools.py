from langchain_core.tools import tool
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import joinedload
from app.core.database import AsyncSessionLocal
from app.models.doctor import Doctor
from app.models.user import User
from app.models.availability import DoctorAvailability
import json


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
    if not days:
        return json.dumps({
            "found": False,
            "message": "No days provided. Please specify which days to check.",
            "doctors": []
        })
    
    if not specialist_type or specialist_type.strip() in ["", "any", "all", "doctor", "doctors"]:
        return json.dumps({
            "found": False,
            "needs_specialty": True,
            "message": "Please specify what type of specialist you are looking for. For example: cardiologist, dentist, dermatologist, neurologist, etc.",
            "doctors": []
        })

    # Normalize capitalization: "monday" → "Monday"
    normalized_days = [d.strip().capitalize() for d in days if d.strip()]

    async with AsyncSessionLocal() as session:
        # Single DB query — fetch doctors available on ANY of the requested days.
        # or_() creates: WHERE days_of_week ILIKE '%Monday%' OR ILIKE '%Wednesday%' ...
        result = await session.execute(
            select(Doctor)
            .join(Doctor.user)
            .join(Doctor.availabilities)
            .options(
                joinedload(Doctor.user),
                joinedload(Doctor.availabilities)
            )
            .where(
                and_(
                    Doctor.specialization.ilike(f"%{specialist_type}%"),
                    Doctor.is_available == True,
                    User.is_verified == True,
                    User.is_active == True,
                    or_(
                        *[
                            DoctorAvailability.days_of_week.ilike(f"%{day}%")
                            for day in normalized_days
                        ]
                    )
                )
            )
            .distinct()
        )
        doctors = result.unique().scalars().all()

        if not doctors:
            days_str = ", ".join(normalized_days)
            return json.dumps({
                "found": False,
                "message": f"No {specialist_type} doctors found available on {days_str}. Try different days or a different specialty.",
                "doctors": []
            })

        # For each doctor, group their available slots by day.
        # Only include slots for the days the user asked about.
        output = []
        for doctor in doctors:
            slots_by_day = {}
            for day in normalized_days:
                day_slots = [
                    {
                        "availability_id": str(av.id),
                        "start_time": av.start_time.strftime("%I:%M %p"),
                        "end_time": av.end_time.strftime("%I:%M %p"),
                    }
                    for av in doctor.availabilities
                    if day.lower() in av.days_of_week.lower()
                ]
                if day_slots:
                    slots_by_day[day] = day_slots

            # Only include this doctor if they have at least one slot
            # on one of the requested days
            if slots_by_day:
                output.append({
                    "doctor_id": str(doctor.id),
                    "name": doctor.user.full_name,
                    "specialization": doctor.specialization,
                    "experience_years": doctor.years_of_experience,
                    "consultation_fee": doctor.consultation_fee,
                    "bio": doctor.bio,
                    "slots_by_day": slots_by_day,
                    "days_available": list(slots_by_day.keys())
                })

        if not output:
            return json.dumps({
                "found": False,
                "message": f"No {specialist_type} doctors have slots on the requested days.",
                "doctors": []
            })

        return json.dumps({
            "found": True,
            "queried_days": normalized_days,
            "doctors": output
        })


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
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Doctor.specialization)
            .join(Doctor.user)
            .where(
                Doctor.is_available == True,
                User.is_active == True,
                User.is_verified.is_(True),
            )
            .distinct()
        )
        specializations = [row[0] for row in result.fetchall()]

        return json.dumps({
            "specializations": specializations,
            "count": len(specializations)
        })