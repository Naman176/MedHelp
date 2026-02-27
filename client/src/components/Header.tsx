import React from "react";
import { Link } from "react-router-dom";
import type { AuthProps } from "../types";

const Header: React.FC<AuthProps> = ({
  isLoggedIn,
  userInfo,
  handleLogout,
}) => (
  <header className="header">
    <div className="logo">
      <Link to="/">MedHelp</Link>
    </div>
    <div className="header-right">
      {isLoggedIn ? (
        <div className="header-icons">
          <div className="icon-group">
            <span className="icon-btn" title="Notifications">
              🔔
            </span>
            <div className="profile-avatar" title="Profile">
              <img
                src={
                  userInfo?.profilePic ||
                  "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
                }
                alt="Profile"
              />
            </div>
          </div>
          <button className="btn-logout" onClick={handleLogout}>
            Logout
          </button>
        </div>
      ) : (
        <div className="auth-btns">
          <Link to="/login" className="btn-ghost">
            Login
          </Link>
          <Link to="/register" className="btn-primary">
            Register
          </Link>
        </div>
      )}
    </div>
  </header>
);

export default Header;
