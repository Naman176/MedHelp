import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";
import type { Appointment } from "../../types";

interface PendingState {
  appointments: Appointment[];
  initialized: boolean;
}

const initialState: PendingState = {
  appointments: [],
  initialized: false
};

const pendingAppointmentsSlice = createSlice({
  name: "pendingAppointments",
  initialState,
  reducers: {
    setPendingAppointments(state, action: PayloadAction<Appointment[]>) {
      state.appointments = action.payload;
      state.initialized = true;
    },

    removePendingAppointment(state, action: PayloadAction<string>) {
      state.appointments = state.appointments.filter(
        a => a.id !== action.payload
      );
    }
  }
});

export const {
  setPendingAppointments,
  removePendingAppointment
} = pendingAppointmentsSlice.actions;

export default pendingAppointmentsSlice.reducer;