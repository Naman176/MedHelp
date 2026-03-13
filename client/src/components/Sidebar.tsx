import React from "react";
import { NavLink } from "react-router-dom";
import {
  Calendar,
  Check,
  Users,
  FileText,
  Settings,
  Clock,
} from "lucide-react";
import "../styles/Sidebar.css";
import { useSelector } from "react-redux";
import { getUserInfo } from "../redux/selectors/rootSelectors";

interface NavItem {
  name: string;
  path: string;
  icon: React.ReactNode;
}

const Sidebar: React.FC = () => {
  const userInfo = useSelector(getUserInfo);
  let applyAsDoctor = null;
  let doctorSidebarRoutes = [];
  let adminSidebarRoutes = [];
  if (userInfo?.role !== "doctor") {
    applyAsDoctor = {
      name: "Apply as Doctor", 
      path: "/apply", 
      icon: <FileText size={20} /> 
    };
  }
  if (userInfo?.role === "admin"){
    adminSidebarRoutes.push({name: "Review Pending Doctor Requests", path: "/reviewDoctors", icon: <Check size={20}/>},
      {name: "Get All Users", path: "/allUsers", icon: <Users size={20}/>},
    )
  }
  if(userInfo?.role === "doctor"){
    doctorSidebarRoutes.push({name: "Approve Appointments", path: "/approveAppointments", icon: <Check size={20}/>},
      {name: "Set Availability", path: "/setAvailability", icon: <Clock size={20}/>}
    )
  }
  const navItems: NavItem[] = [
    {
      name: "Appointments",
      path: "/appointments",
      icon: <Calendar size={20} />,
    },
    { name: "View Doctors", path: "/doctors", icon: <Users size={20} /> },
    ...(applyAsDoctor ? [applyAsDoctor] : []),
    ...(adminSidebarRoutes ? adminSidebarRoutes : []),
    ...(doctorSidebarRoutes ? doctorSidebarRoutes : [])
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
