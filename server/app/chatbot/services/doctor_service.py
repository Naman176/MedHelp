import json
from uuid import UUID
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload
from app.core.database import AsyncSessionLocal
from app.models.appointment import Appointment
from app.models.availability import DoctorAvailability
from app.models.doctor import Doctor
from app.models.user import User


async def list_available_specializations() -> dict:
    """
    Return all unique specializations for verified, active, available doctors.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Doctor.specialization)
            .join(Doctor.user)
            .where(
                Doctor.is_available.is_(True),
                User.is_active.is_(True),
                User.is_verified.is_(True),
            )
            .distinct()
        )

        specializations = sorted(set(result.scalars().all()))

        return {
            "specializations": specializations,
            "count": len(specializations),
        }


async def search_available_doctors(specialist_type: str, days: list[str]) -> dict:
    """
    Return doctors for a specialty and list of days.
    """
    if not days:
        return {
            "found": False,
            "message": "No days provided.",
            "doctors": [],
        }

    normalized_days = [
        day.strip().capitalize()
        for day in days
        if day and day.strip()
    ]

    if not normalized_days:
        return {
            "found": False,
            "message": "No valid days provided.",
            "doctors": [],
        }

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Doctor)
            .join(Doctor.user)
            .join(Doctor.availabilities)
            .options(
                joinedload(Doctor.user),
                joinedload(Doctor.availabilities),
            )
            .where(
                Doctor.specialization.ilike(f"%{specialist_type}%"),
                Doctor.is_available.is_(True),
                User.is_active.is_(True),
                User.is_verified.is_(True),
                or_(
                    *[
                        DoctorAvailability.days_of_week.ilike(f"%{day}%")
                        for day in normalized_days
                    ]
                ),
            )
            .distinct()
        )

        doctors = result.unique().scalars().all()

        if not doctors:
            return {
                "found": False,
                "message": f"No {specialist_type} doctors found on {', '.join(normalized_days)}.",
                "doctors": [],
            }

        output = []

        for doctor in doctors:
            slots_by_day = {}

            for day in normalized_days:
                matching_slots = [
                    {
                        "availability_id": str(av.id),
                        "start_time": av.start_time.strftime("%I:%M %p"),
                        "end_time": av.end_time.strftime("%I:%M %p"),
                    }
                    for av in doctor.availabilities
                    if day.lower() in av.days_of_week.lower()
                ]

                if matching_slots:
                    slots_by_day[day] = matching_slots

            if slots_by_day:
                output.append(
                    {
                        "doctor_id": str(doctor.id),
                        "name": doctor.user.full_name if doctor.user else None,
                        "specialization": doctor.specialization,
                        "experience_years": doctor.years_of_experience,
                        "consultation_fee": doctor.consultation_fee,
                        "bio": doctor.bio,
                        "days_available": list(slots_by_day.keys()),
                        "slots_by_day": slots_by_day,
                    }
                )

        if not output:
            return {
                "found": False,
                "message": f"No {specialist_type} doctors available on the requested days.",
                "doctors": [],
            }

        return {
            "found": True,
            "queried_days": normalized_days,
            "doctors": output,
        }
