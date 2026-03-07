import { configureStore } from "@reduxjs/toolkit";
import rootReducer from "./reducers/rootSlice";
import notificationsReducer from './reducers/notificationsSlice'
import { authApi } from "./services/authApi";

export const store = configureStore({
  reducer: {
    notifications: notificationsReducer,
    root: rootReducer,
    [authApi.reducerPath]: authApi.reducer,
  },

  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(authApi.middleware),
});

store.subscribe(() => {
  localStorage.setItem(
    "notifications",
    JSON.stringify(store.getState().notifications)
  );
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export default store;