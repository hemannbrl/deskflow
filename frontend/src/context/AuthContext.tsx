"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { api } from "../lib/api";
import * as auth from "../lib/auth";
import { getAccessToken } from "../lib/tokens";
import type { User } from "../lib/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const restore = getAccessToken()
      ? api<User>("/api/v1/me/")
          .then(setUser)
          .catch(() => auth.logout())
      : Promise.resolve();
    restore.finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    await auth.login(username, password);
    setUser(await api<User>("/api/v1/me/"));
  }, []);

  const register = useCallback(
    async (username: string, email: string, password: string) => {
      await auth.register(username, email, password);
      setUser(await api<User>("/api/v1/me/"));
    },
    [],
  );

  const logout = useCallback(() => {
    auth.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
