import { useEffect } from "react";
import { jwtDecode } from "jwt-decode";
import axios from "axios";
import { useDispatch, useSelector } from "react-redux";
import { addNotification, setNotifications } from "../redux/reducers/notificationsSlice";
import type { RootState } from "../redux/store";
import type { Notification } from "../types";

const API_URL = import.meta.env.VITE_SERVER_DOMAIN;
const WS_URL = "ws://localhost:8000/notifications/ws";

interface JwtPayload {
  id: string;
  sub: string;
  role: string;
}

export const useNotifications = (token: string | null) => {
  const dispatch = useDispatch();
  const { initialized } = useSelector((state: RootState) => state.notifications);

  useEffect(() => {
    if (!token) return;
    const decoded = jwtDecode<JwtPayload>(token);
    const userId = decoded.id;
    console.log(jwtDecode(token));
    const storedItem = localStorage.getItem("notifications");
    let storedNotifications: Notification[] = [];
    const parsed = storedItem ? JSON.parse(storedItem) : [];
    storedNotifications = Array.isArray(parsed) ? parsed : [];
    const init = async () => {
      try {
        const res = await axios.get<Notification[]>(`${API_URL}/notifications`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        // Merge read flags from localStorage
        const merged = res.data.map((n) => {
          const stored = storedNotifications.find((s) => s.id === n.id);
          return stored ? { ...n, is_read: stored.is_read } : n;
        });

        dispatch(setNotifications(merged));
        localStorage.setItem("notifications", JSON.stringify(merged));
      } catch (err) {
        console.error("Failed to fetch notifications", err);
      }
    };

    init();

    const ws = new WebSocket(`${WS_URL}/${userId}`);

    ws.onmessage = (event) => {
       const notif: Notification = JSON.parse(event.data);
        dispatch(addNotification(notif));

        const updated = [notif, ...JSON.parse(localStorage.getItem("notifications") || "[]")];
        localStorage.setItem("notifications", JSON.stringify(updated));
    };

    ws.onerror = (err) => {
      console.error("WebSocket error", err);
    };

    return () => ws.close();
  }, [dispatch, token, initialized]);
};