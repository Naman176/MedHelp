import { useEffect } from "react";
import { jwtDecode } from "jwt-decode";
import axios from "axios";
import { useDispatch } from "react-redux";
import { addNotification, setNotifications } from "../redux/reducers/notificationsSlice";
import type { Notification } from "../types";
import fetchData from "../helper/apiCall";
import { setPendingAppointments } from "../redux/reducers/pendingAppointmentSlice";

const API_URL = import.meta.env.VITE_SERVER_DOMAIN || "http://localhost:8000";
const getWebSocketBaseUrl = (): string => {
  return API_URL.replace(/^http/, "ws");
};
const WS_URL = `${getWebSocketBaseUrl()}/notifications/ws`;

interface JwtPayload {
  id?: string;
  sub: string;
  role: string;
}

export const useNotifications = (token: string | null) => {
  const dispatch = useDispatch();

  useEffect(() => {
    if (!token) return;
    let decoded: JwtPayload;
    try {
      decoded = jwtDecode<JwtPayload>(token);
    } catch {
      console.error("Invalid JWT token; notifications disabled.");
      return;
    }

    const userId = decoded.id;
    if (!userId) {
      console.error("JWT does not contain user id; notifications disabled.");
      return;
    }

    let storedNotifications: Notification[] = [];
    try {
      const storedItem = localStorage.getItem("notifications");
      const parsed = storedItem ? JSON.parse(storedItem) : [];
      storedNotifications = Array.isArray(parsed) ? parsed : [];
    } catch {
      storedNotifications = [];
    }

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

    ws.onmessage = async (event) => {
       try {
        const notif: Notification = JSON.parse(event.data);

        dispatch(addNotification(notif));

        if (notif.title === "New Booking Request") {
          const res = await fetchData("/appointments/pendingAppointments");
          dispatch(setPendingAppointments(res));
        }

        let current: Notification[] = [];

        try {
          const parsed = JSON.parse(localStorage.getItem("notifications") || "[]");
          current = Array.isArray(parsed) ? parsed : [];
        } catch {
          current = [];
        }

        const updated = [notif, ...current];
        localStorage.setItem("notifications", JSON.stringify(updated));
      } catch (error) {
        console.error("Failed to handle websocket notification", error);
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error", err);
    };

    return () => ws.close();
  }, [dispatch, token]);
};