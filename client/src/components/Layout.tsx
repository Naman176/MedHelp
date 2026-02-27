import React from "react";
import Header from "./Header";
import Sidebar from "./Sidebar";
import Footer from "./Footer";
import type { AuthProps } from "../types";

interface LayoutProps extends AuthProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({
  children,
  isLoggedIn,
  userInfo,
  handleLogout,
}) => {
  return (
    <div className="main-layout">
      <Header
        isLoggedIn={isLoggedIn}
        userInfo={userInfo}
        handleLogout={handleLogout!}
      />

      <div className="middle-section">
        {isLoggedIn && <Sidebar />}
        <main className="content-container">{children}</main>
      </div>

      <Footer />
    </div>
  );
};

export default Layout;
