import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";
import type { UserInfo, Appointment, Doctor } from "../../types";

interface RootState {
  loading: boolean;
  userInfo: UserInfo | null;
  appointments: Appointment[];
  doctors: Doctor[]
}

const initialState: RootState = {
  loading: true,
  userInfo: {},
  appointments: [],
  doctors: []
};

export const rootReducer = createSlice({
  name: "root",
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setUserInfo: (state, action: PayloadAction<UserInfo | null>) => {
      state.userInfo = action.payload;
    },
    setAppointments: (state, action: PayloadAction<Appointment[]>) => {
      state.appointments = action.payload;
    },
    setDoctors: (state, action: PayloadAction<Doctor[]>) => {
      state.doctors = action.payload;
    },
  },
});

export const { setLoading, setUserInfo, setAppointments, setDoctors } = rootReducer.actions;
export default rootReducer.reducer;
