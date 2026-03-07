import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";
import type { Notification } from "../../types";

interface NotificationState {
  notifications: Notification[];
  initialized: boolean;
}

const initialState: NotificationState = {
  notifications: [],
  initialized: false
};

const notificationSlice = createSlice({
  name: "notifications",
  initialState,
  reducers: {
    setNotifications(state, action: PayloadAction<Notification[]>) {
      state.notifications = action.payload;
      state.initialized = true;
    },

    addNotification(state, action: PayloadAction<Notification>) {
      state.notifications.unshift(action.payload);
    },
  }
});

export const { setNotifications, addNotification } =
  notificationSlice.actions;

export default notificationSlice.reducer;