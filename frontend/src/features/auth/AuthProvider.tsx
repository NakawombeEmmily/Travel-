import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";
import { api, clearTokens, getAccessToken, setTokens } from "@/config/api";
import type { UserRole } from "./types";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
}

interface AuthContextValue {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasToken?: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  async function login(email: string, password: string) {
    const res = await api.post<{ access_token: string; refresh_token: string }>(
      "/auth/login",
      { email, password },
    );
    setTokens(res.access_token, res.refresh_token);
    const me = await api.get<User>("/auth/me");
    setUser(me);
  }

  function logout() {
    clearTokens();
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{ user, login, logout, hasToken: !!getAccessToken() }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
