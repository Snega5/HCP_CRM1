import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import StatCard from "../components/StatCard";
import BarChart from "../components/BarChart";
import Loader from "../components/Loader";
import { getDashboardStats } from "../services/dashboardService";
import { getErrorMessage } from "../services/api";

function timeAgo(iso) {
  if (!iso) return "";
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} hr ago`;
  return `${Math.floor(diff / 86400)} d ago`;
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      setStats(await getDashboardStats());
    } catch (err) {
      setError(getErrorMessage(err, "Could not load dashboard data"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (loading) return <Loader text="Loading dashboard..." />;

  if (error) {
    return (
      <div className="card error-card">
        <h3>Dashboard unavailable</h3>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={load}>
          Retry
        </button>
      </div>
    );
  }

  const gender = Object.entries(stats.gender_distribution || {}).map(([label, value]) => ({ label, value }));
  const ages = (stats.age_distribution || []).map((a) => ({ label: a.label, value: a.count }));

  return (
    <div className="dashboard">
      <div className="quick-actions">
        <Link to="/patients" className="btn btn-primary">
          Manage patients
        </Link>
        <Link to="/ai-extractor" className="btn btn-ghost">
          ✦ Extract with AI
        </Link>
      </div>

      <section className="stat-grid">
        <StatCard label="Total patients" value={stats.total_patients} icon="👥" tone="blue" hint="All registered records" />
        <StatCard label="New this week" value={stats.new_this_week} icon="＋" tone="green" hint="Last 7 days" />
        <StatCard label="Appointments today" value={stats.appointments_today} icon="📅" tone="amber" hint="Scheduled for today" />
        <StatCard label="AI extractions" value={stats.ai_extractions} icon="✦" tone="purple" hint="Saved from AI extractor" />
      </section>

      <section className="two-col">
        <div className="card">
          <div className="card-header">
            <h3>Recently added patients</h3>
            <Link to="/patients" className="link">
              View all
            </Link>
          </div>
          {stats.recent_patients?.length ? (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Age</th>
                    <th>Diagnosis</th>
                    <th>Doctor</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.recent_patients.map((p) => (
                    <tr key={p.id}>
                      <td className="muted">{p.patient_code}</td>
                      <td className="strong">{p.full_name}</td>
                      <td>{p.age ?? "—"}</td>
                      <td>{p.diagnosis || "—"}</td>
                      <td>{p.doctor_assigned || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">No patients yet. Add one or use the AI extractor.</div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Recent activity</h3>
          </div>
          {stats.recent_activities?.length ? (
            <ul className="activity-list">
              {stats.recent_activities.map((a) => (
                <li key={a.id}>
                  <span className="activity-dot" />
                  <div>
                    <div className="strong">{a.description}</div>
                    <div className="muted small">{timeAgo(a.created_at)}</div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty-state">No activity recorded yet.</div>
          )}
        </div>
      </section>

      <section className="two-col">
        <div className="card">
          <div className="card-header">
            <h3>Gender distribution</h3>
          </div>
          <BarChart data={gender} />
        </div>
        <div className="card">
          <div className="card-header">
            <h3>Age groups</h3>
          </div>
          <BarChart data={ages} />
        </div>
      </section>
    </div>
  );
}
