import _ from "lodash";
import { GoogleOAuthProvider } from '@react-oauth/google';
import { BrowserRouter as Router, Route, Routes, Link, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import "./styles/app.css";

import { Toaster } from "react-hot-toast";
import { Suspense, useEffect, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { setUserInfo } from "./redux/reducers/rootSlice";
import Appointments from "./pages/Appointments";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

function App() {
  const dispatch = useDispatch();
  // Check if user info exists in Redux store
  const { userInfo } = useSelector((state: any) => state.root); 
  const [loading, setLoading] = useState(true);

  // Determine login status 
  let isLoggedIn = !_.isNil(userInfo) && !_.isEmpty(userInfo)
  console.log(isLoggedIn)
  console.log(userInfo)
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token && !userInfo) {
      setLoading(false);
    } else {
      setLoading(false);
    }
  }, [userInfo]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    dispatch(setUserInfo(null));
    window.location.href = "/";
  };

  if (loading) return <div>Loading MedHelp...</div>;

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <Router>
        <Toaster position="top-center" />
        <Suspense fallback={<div>Loading...</div>}>
          
          <div className="main-layout">
            {/* --- HEADER --- */}
            <header className="header">
              <div className="logo"><Link to="/">MedHelp</Link></div>
              <div className="header-right">
              {isLoggedIn ? (
                <div className="header-icons">
                  <div className="icon-group">
                    <span className="icon-btn" title="Notifications">🔔</span>
                    {/* Profile Circular Avatar */}
                    <div className="profile-avatar" title="Profile">
                      <img 
                        src={userInfo?.profilePic || "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"} 
                        alt="Profile" 
                      />
                    </div>
                  </div>
                  <button className="btn-logout" onClick={handleLogout}>Logout</button>
                </div>
              ) : (
                <div className="auth-btns">
                  <Link to="/login" className="btn-ghost">Login</Link>
                  <Link to="/register" className="btn-primary">Register</Link>
                </div>
              )}
            </div>
            </header>

            <div className="middle-section">
              {/* --- LEFT PANE (Only if Logged In) --- */}
              {isLoggedIn && (
                <aside className="left-pane">
                  <nav className="side-nav">
                    <Link to="/appointments" className="nav-item">Your Appointments</Link>
                    <Link to="/doctors" className="nav-item">View All Doctors</Link>
                    <Link to="/apply" className="nav-item">Apply for Doctor</Link>
                  </nav>
                </aside>
              )}

              {/* --- CONTENT AREA --- */}
              <main className="content-container">
                <Routes>
                  <Route path="/login" element={!isLoggedIn ? <Login /> : <Navigate to="/" />} />
                  <Route path="/register" element={!isLoggedIn ? <Register /> : <Navigate to="/" />} />

                  <Route 
                    path="/" 
                    element={
                      isLoggedIn ? (
                        <div className="page-content"><h2>Your Appointments</h2><p>Welcome to your medical dashboard.</p></div>
                      ) : (
                        <div className="landing-page">
                          <h1>Your Health, Our Priority</h1>
                          <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
                        </div>
                      )
                    } 
                  />
                  
                  <Route path="/appointments" element={isLoggedIn ? <Appointments/> : <Navigate to="/login" />} />
                  <Route path="/doctors" element={isLoggedIn ? <div className="page-content"><h2>All Doctors</h2></div> : <Navigate to="/login" />} />
                  <Route path="/apply" element={isLoggedIn ? <div className="page-content"><h2>Apply for Doctor</h2></div> : <Navigate to="/login" />} />
                </Routes>
              </main>
            </div>

            {/* --- FOOTER --- */}
            <footer className="footer">
              <div className="footer-content">
                <span className="contact-sign">Contact Us</span>
                <div className="social-links">
                  <a href="#">Instagram</a>
                  <a href="#">Facebook</a>
                  <a href="#">Twitter</a>
                </div>
              </div>
            </footer>
          </div>

        </Suspense>
      </Router>
    </GoogleOAuthProvider>
  );
}

export default App;