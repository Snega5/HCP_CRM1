import React from "react";

// Simple horizontal bar chart built with CSS (no chart library needed)
export default function BarChart({ data, emptyText = "No data yet" }) {
  const max = Math.max(...data.map((d) => d.value), 0);
  if (!data.length || max === 0) return <div className="empty-state">{emptyText}</div>;

  return (
    <div className="bar-chart">
      {data.map((d) => (
        <div className="bar-row" key={d.label}>
          <span className="bar-label">{d.label}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(d.value / max) * 100}%` }} />
          </div>
          <span className="bar-value">{d.value}</span>
        </div>
      ))}
    </div>
  );
}
