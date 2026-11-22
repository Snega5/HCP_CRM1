import api from "./api";

// POST /api/auth/login  -> { access_token, token_type, user: { id, username, full_name, role } }
export async function loginUser(username, password) {
  const res = await api.post("/auth/login", { username, password });
  return res.data;
}
