import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  api,
  clearTokens,
  getAccessToken,
  SESSION_EXPIRED_EVENT,
  setTokens,
} from "@/config/api";
import type { UserRole } from "./types";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
}

export interface RegisterPayload {
  email: string;
  full_name: string;
  password: string;
}

interface AuthContextValue {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  hasToken?: boolean;
  initializing: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [initializing, setInitializing] = useState<boolean>(
    () => !!getAccessToken(),
  );

  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener(SESSION_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired);
  }, []);

  useEffect(() => {
    if (!getAccessToken()) {
      setInitializing(false);
      return;
    }
    let active = true;
    api
      .get<User>("/auth/me")
      .then((me) => {
        if (active) setUser(me);
      })
      .catch(() => {
        if (active) {
          clearTokens();
          setUser(null);
        }
      })
      .finally(() => {
        if (active) setInitializing(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function establishSession(path: string, body: unknown) {
    const res = await api.post<{ access_token: string; refresh_token: string }>(
      path,
      body,
    );
    setTokens(res.access_token, res.refresh_token);
    const me = await api.get<User>("/auth/me");
    setUser(me);
  }

  async function login(email: string, password: string) {
    await establishSession("/auth/login", { email, password });
  }

  async function register(payload: RegisterPayload) {
    await establishSession("/auth/register", payload);
  }

  function logout() {
    clearTokens();
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        register,
        logout,
        hasToken: !!getAccessToken(),
        initializing,
      }}
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
