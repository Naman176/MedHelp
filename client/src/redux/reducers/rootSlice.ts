import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";

interface RootState {
  loading: boolean;
  userInfo: any; // 👈 you can replace `any` with a proper User interface later
}

const initialState: RootState = {
  loading: true,
  userInfo: {},
};

export const rootReducer = createSlice({
  name: "root",
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setUserInfo: (state, action: PayloadAction<any>) => {
      state.userInfo = action.payload;
    },
  },
});

export const { setLoading, setUserInfo } = rootReducer.actions;
export default rootReducer.reducer;