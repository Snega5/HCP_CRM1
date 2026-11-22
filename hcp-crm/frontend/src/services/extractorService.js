import api from "./api";

// POST /api/extract { text } -> { extracted: { patient_name, age, gender, ... }, model }
// Nothing is saved by this call; the user reviews the result first.
export async function extractPatientInfo(text) {
  const res = await api.post("/extract", { text }, { timeout: 60000 });
  return res.data;
}
