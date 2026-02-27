import React, { Suspense, useEffect, useState } from "react";
import _ from "lodash";
import { GoogleOAuthProvider } from '@react-oauth/google';
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { Toaster } from "react-hot-toast";

import { Protected, Public } from "./middleware/route"; 
import { setUserInfo } from "./redux/reducers/rootSlice";
import { getUserInfo } from "./redux/selectors/rootSelectors";
import type { UserInfo } from "./types";

import Layout from "./components/Layout";
import Dashboard from "./components/Dashboard";
import Login from "./components/Login";
import Register from "./components/Register";
import Appointments from "./components/Appointments";

import "./styles/app.css";
import Doctors from "./components/Doctors";

const GOOGLE_CLIENT_ID: string = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

const App: React.FC = () => {
  const dispatch = useDispatch();
  const userInfo = useSelector(getUserInfo) as UserInfo | null; 
  const [loading, setLoading] = useState<boolean>(true);

  const isLoggedIn: boolean = !_.isNil(userInfo) && !_.isEmpty(userInfo);

  useEffect(() => {
    setLoading(false);
  }, [userInfo]);

  const handleLogout = (): void => {
    localStorage.removeItem("token");
    dispatch(setUserInfo(null));
    window.location.href = "/";
  };

  if (loading) return <div className="loading-screen">Loading MedHelp...</div>;

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
            </Routes>
          </Layout>

        </Suspense>
      </Router>
    </GoogleOAuthProvider>
  );
}

export default App;