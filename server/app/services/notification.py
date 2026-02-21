from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.notification import Notification
from app.core.ws_manager import manager
from app.schemas.notification import NotificationResponse

async def send_notification(
    db: AsyncSession,
    user_id: UUID,
    title: str,
    message: str,
    notification_type: str
):
    # 1. Save it permanently to the database
    new_notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type
    )
    db.add(new_notification)
    await db.commit()
    await db.refresh(new_notification)

    # 2. Convert the SQLAlchemy model into a clean JSON dictionary
    notif_data = NotificationResponse.model_validate(new_notification).model_dump(mode='json')
    
    # 3. Push it directly to the user if they are currently online!
    await manager.send_personal_message(notif_data, user_id)