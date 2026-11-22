import React from "react";

export default function StatCard({ label, value, hint, icon, tone = "blue" }) {
  return (
    <div className="card stat-card">
      <div className={`stat-icon tone-${tone}`}>{icon}</div>
      <div>
        <div className="stat-label">{label}</div>
        <div className="stat-value">{value}</div>
        {hint && <div className="stat-hint">{hint}</div>}
      </div>
    </div>
  );
}
