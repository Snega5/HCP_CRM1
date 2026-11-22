import React from "react";
import { useLocation } from "react-router-dom";

const TITLES = {
  "/dashboard": "Dashboard",
  "/patients": "Patients",
  "/ai-extractor": "AI Patient Data Extractor",
};

export default function Topbar({ onMenuClick }) {
  const { pathname } = useLocation();
  const today = new Date().toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <header className="topbar">
      <button className="menu-btn" onClick={onMenuClick} aria-label="Open menu">
        ☰
      </button>
      <h1 className="topbar-title">{TITLES[pathname] || "HCP CRM"}</h1>
      <span className="topbar-date">{today}</span>
    </header>
  );
}
