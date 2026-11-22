import api from "./api";

/**
 * GET /api/dashboard/stats
 * Expected response shape (the backend stage implements this contract):
 * {
 *   total_patients: number,
 *   new_this_week: number,
 *   appointments_today: number,
 *   ai_extractions: number,
 *   gender_distribution: { Male: number, Female: number, Other: number },
 *   age_distribution: [{ label: "0-17", count: number }, ...],
 *   recent_patients: [{ id, patient_code, full_name, age, gender, diagnosis, doctor_assigned, created_at }],
 *   recent_activities: [{ id, action, description, created_at }]
 * }
 */
export async function getDashboardStats() {
  const res = await api.get("/dashboard/stats");
  return res.data;
}
