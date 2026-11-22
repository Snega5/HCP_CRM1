import api from "./api";

// GET /api/patients?q=&skip=&limit=  -> { items: [...], total }
export async function listPatients({ q = "", skip = 0, limit = 10 } = {}) {
  const res = await api.get("/patients", { params: { q: q || undefined, skip, limit } });
  return res.data;
}

export async function getPatient(id) {
  const res = await api.get(`/patients/${id}`);
  return res.data;
}

export async function createPatient(data) {
  const res = await api.post("/patients", data);
  return res.data;
}

export async function updatePatient(id, data) {
  const res = await api.put(`/patients/${id}`, data);
  return res.data;
}

export async function deletePatient(id) {
  await api.delete(`/patients/${id}`);
}
