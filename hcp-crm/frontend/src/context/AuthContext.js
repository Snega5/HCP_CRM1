import React, { createContext, useContext, useState, useCallback } from "react";
import { loginUser } from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("hcp_user"));
    } catch {
      return null;
    }
  });

  const login = useCallback(async (username, password) => {
    const data = await loginUser(username, password);
    localStorage.setItem("hcp_token", data.access_token);
    localStorage.setItem("hcp_user", JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("hcp_token");
    localStorage.removeItem("hcp_user");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
