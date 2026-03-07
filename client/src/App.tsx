import React, { Suspense, useEffect } from "react";
import _ from "lodash";
import { GoogleOAuthProvider } from '@react-oauth/google';
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { Toaster } from "react-hot-toast";

import { Admin, Protected, Public } from "./middleware/route"; 
import { setUserInfo } from "./redux/reducers/rootSlice";
import { getUserInfo } from "./redux/selectors/rootSelectors";
import type { UserInfo } from "./types";
import { useNotifications } from "./hooks/useNotifications";

import Layout from "./components/Layout";
import Dashboard from "./components/Dashboard";
import Login from "./components/Login";
import Register from "./components/Register";
import Appointments from "./components/Appointments";

import "./styles/app.css";
import Doctors from "./components/Doctors";
import BookAppointment from "./components/BookAppointment";
import ApplyAsDoctor from "./components/ApplyAsDoctor";
import ReviewDoctors from "./components/ReviewDoctors";
import { useGetMeQuery } from "./redux/services/authApi";
import AllUsers from "./components/AllUsers";

const GOOGLE_CLIENT_ID: string = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";
console.log('gci', GOOGLE_CLIENT_ID)
const App: React.FC = () => {
  const dispatch = useDispatch();
  const userInfo = useSelector(getUserInfo) as UserInfo | null; 
  const token = localStorage.getItem("token")
  useNotifications(token);
  const isLoggedIn: boolean =  token ? true : false;

  const { data: userDetails, isLoading, isError } = useGetMeQuery(undefined, {
    skip: !token,
  });

  useEffect(() => {
    if (userDetails) {
      dispatch(setUserInfo(userDetails));
    }
    if (isError) {
      localStorage.removeItem("token");
      dispatch(setUserInfo(null));
    }
  }, [userDetails, isError, dispatch]);


  const handleLogout = (): void => {
    localStorage.removeItem("token");
    dispatch(setUserInfo(null));
    window.location.href = "/";
  };
  const isVerifyingSession = !!token && isLoading;

  if (isVerifyingSession) return <div className="loading-screen">Loading MedHelp...</div>;

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <Router>
        <Toaster position="top-center" />
        <Suspense fallback={<div className="loading-screen">Loading...</div>}>
          
          <Layout isLoggedIn={isLoggedIn} userInfo={userInfo} handleLogout={handleLogout}>
            <Routes>
              <Route path="/login" element={<Public><Login /></Public>} />
              <Route path="/register" element={<Public><Register /></Public>} />
              <Route path="/" element={<Dashboard isLoggedIn={isLoggedIn} userInfo={userInfo} />} />
              
              <Route path="/appointments" element={<Protected><Appointments /></Protected>} />
              <Route path="/doctors" element={
                <Protected>
                  <Doctors/>
                </Protected>
              } />
              <Route path="/book-appointment/:doctorId" element={
                <Protected>
                  <BookAppointment />
                </Protected>
              } />
              <Route path="/apply" element={
                <Protected>
                  <ApplyAsDoctor/>
                </Protected>
              } />
              <Route path="/reviewDoctors" element={
                <Admin>
                  <ReviewDoctors/>
                </Admin>
              } />
              <Route path="/allUsers" element={
                <Admin>
                  <AllUsers/>
                </Admin>
              } />
            </Routes>
          </Layout>

        </Suspense>
      </Router>
    </GoogleOAuthProvider>
  );
}

export default App;