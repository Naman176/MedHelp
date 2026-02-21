from pydantic import BaseModel, ConfigDict
from typing import Literal
from uuid import UUID
from datetime import datetime

class NotificationCreate(BaseModel):
    user_id: UUID
    title: str
    message: str
    notification_type: Literal["INFO", "SUCCESS", "WARNING", "ERROR", "REMINDER"] 

class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)