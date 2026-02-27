import React from "react";
import { NavLink } from "react-router-dom";
import {
  Calendar,
  Users,
  FileText,
  LayoutDashboard,
  Settings,
} from "lucide-react";
import "../styles/Sidebar.css";

interface NavItem {
  name: string;
  path: string;
  icon: React.ReactNode;
}

const Sidebar: React.FC = () => {
  const navItems: NavItem[] = [
    { name: "Dashboard", path: "/", icon: <LayoutDashboard size={20} /> },
    {
      name: "Appointments",
      path: "/appointments",
      icon: <Calendar size={20} />,
    },
    { name: "View Doctors", path: "/doctors", icon: <Users size={20} /> },
    { name: "Apply as Doctor", path: "/apply", icon: <FileText size={20} /> },
  ];

  return (
    <aside className="sidebar">
      <nav className="side-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `nav-item ${isActive ? "active-link" : ""}`
            }
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* Optional: Bottom section for settings or help */}
      <div className="sidebar-footer">
        <NavLink to="/settings" className="nav-item">
          <Settings size={20} />
          <span className="nav-label">Settings</span>
        </NavLink>
      </div>
    </aside>
  );
};

export default Sidebar;
