from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.ws_manager import manager
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

# THE WEBSOCKET ENDPOINT (Real-Time Connection)
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: UUID):
    """
    Frontend connects to this URL (e.g., ws://localhost:8000/notifications/ws/1234-abcd)
    Note: Standard browser WebSockets can't send Auth Headers easily, 
    so passing the user_id (or a secure token) in the URL is standard practice.
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keeps the connection open listening for client messages (if any)
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)


# GET ALL NOTIFICATIONS (Historical Data)
@router.get("/", response_model=List[NotificationResponse])
async def get_my_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Notification]:
    """Fetch all past notifications for the logged-in user."""
    query = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
    )
    return list(query.scalars().all())


# MARK AS READ
@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Notification:
    """Marks a specific notification as read when the user clicks it."""
    query = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = query.scalars().first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    
    return notification