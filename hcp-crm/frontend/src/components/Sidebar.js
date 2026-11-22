import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: "▦" },
  { to: "/patients", label: "Patients", icon: "☰" },
  { to: "/ai-extractor", label: "AI Extractor", icon: "✦" },
];

export default function Sidebar({ open, onClose }) {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
      <div className="sidebar-brand">
        <span className="brand-logo">+</span>
        <div>
          <div className="brand-name">HCP CRM</div>
          <div className="brand-sub">Healthcare Suite</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onClose}
            className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="avatar">{(user?.full_name || user?.username || "U").charAt(0).toUpperCase()}</div>
          <div>
            <div className="user-name">{user?.full_name || user?.username}</div>
            <div className="user-role">{user?.role || "Staff"}</div>
          </div>
        </div>
        <button className="btn btn-ghost btn-block" onClick={handleLogout}>
          Log out
        </button>
      </div>
    </aside>
  );
}
