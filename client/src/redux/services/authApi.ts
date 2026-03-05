import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

const baseUrl = import.meta.env.VITE_SERVER_DOMAIN as string;
export const authApi = createApi({
  reducerPath: "authApi",
  baseQuery: fetchBaseQuery({
    baseUrl: baseUrl,
    prepareHeaders: (headers) => {
      const token = localStorage.getItem("token");
      if (token) headers.set("authorization", `Bearer ${token}`);
      return headers;
    },
  }),
  endpoints: (builder) => ({
    getMe: builder.query<any, void>({
      query: () => "/user/me",
      // This transforms the snake_case backend to camelCase frontend automatically
      transformResponse: (response: any) => ({
        fullName: response.full_name,
        profilePic: response.profile_picture,
        role: response.role,
        email: response.email,
      }),
    }),
  }),
});

export const { useGetMeQuery } = authApi;