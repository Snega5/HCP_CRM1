import axios from "axios";

// Base URL of the FastAPI backend. Override in frontend/.env (see .env.example).
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Attach the JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("hcp_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Log the user out automatically if the token is rejected
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response && error.response.status === 401 && !error.config.url.includes("/auth/login")) {
      localStorage.removeItem("hcp_token");
      localStorage.removeItem("hcp_user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Turn any axios error into a readable message
export function getErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  if (error.response?.data?.detail) {
    const d = error.response.data.detail;
    return typeof d === "string" ? d : JSON.stringify(d);
  }
  if (error.code === "ERR_NETWORK") return "Cannot reach the server. Is the backend running on port 8000?";
  return error.message || fallback;
}

export default api;
