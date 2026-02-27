import type { RootState } from "../store"; // 👈 your actual store type

export const getLoading = (state: RootState) => state.root.loading;

export const getUserInfo = (state: RootState) => state.root.userInfo;

export const getAppointments = (state: RootState) => state.root.appointments;

export const getDoctors = (state: RootState) => state.root.doctors
