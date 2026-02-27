import React from "react";
import type { AuthProps } from "../types";

const Dashboard: React.FC<AuthProps> = ({ isLoggedIn, userInfo }) => {
  if (isLoggedIn) {
    return (
      <div className="page-content">
        <h2>Medical Dashboard</h2>
        <p>
          Welcome back, {userInfo?.fullName || "User"}. Select an option from
          the sidebar.
        </p>
      </div>
    );
  }

  return (
    <div className="landing-page">
      <h1>Your Health, Our Priority</h1>
      <p>Providing world-class medical assistance at your fingertips.</p>
    </div>
  );
};

export default Dashboard;
