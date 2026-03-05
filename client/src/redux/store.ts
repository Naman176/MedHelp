import { configureStore } from "@reduxjs/toolkit";
import rootReducer from "./reducers/rootSlice";
import { authApi } from "./services/authApi";

export const store = configureStore({
  reducer: {
    root: rootReducer,
    [authApi.reducerPath]: authApi.reducer,
  },

  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(authApi.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export default store;