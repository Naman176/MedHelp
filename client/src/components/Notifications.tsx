import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import type { RootState } from "../redux/store";
import type { Notification } from "../types";
import "../styles/Notifications.css";
import { patchData } from "../helper/apiCall";
import { setNotifications } from "../redux/reducers/notificationsSlice";

const Notifications = () => {

  const [isOpen, setIsOpen] = useState(false);
  const dispatch = useDispatch()
  const notifications = useSelector(
    (state: RootState) => state.notifications.notifications
  );

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const handleToggle = () => {
    const newState = !isOpen;
    setIsOpen(newState);
  };

    const handleMarkRead = async (notif: Notification) => {
    if (notif.is_read) return; // already read

    try {
      await patchData(`/notifications/${notif.id}/read`,{})

      // update local Redux state
      const updatedNotifications = notifications.map((n) =>
        n.id === notif.id ? { ...n, is_read: true } : n
      );

      dispatch(setNotifications(updatedNotifications));

      // update localStorage
      localStorage.setItem("notifications", JSON.stringify(updatedNotifications));
    } catch (err) {
      console.error("Failed to mark notification as read", err);
    }
  };
  return (
    <div className="notification-wrapper">
      <span className="icon-btn" onClick={handleToggle}>
        🔔
        {unreadCount > 0 && (
          <span className="notif-badge">{unreadCount}</span>
        )}
      </span>

      {isOpen && (
        <div className="notif-dropdown">
          {notifications.length === 0 ? (
            <div className="notif-empty">No new notifications</div>
          ) : (
            notifications.map((notif) => (
              <div
                key={notif.id}
                className={`notif-item ${notif.is_read ? "" : "unread"}` }
                onClick={() => handleMarkRead(notif)}
              >
                <div className="notif-title">{notif.title}</div>
                <div className="notif-message">{notif.message}</div>
                <div className="notif-time">
                  {new Date(notif.created_at).toLocaleString()}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default Notifications;