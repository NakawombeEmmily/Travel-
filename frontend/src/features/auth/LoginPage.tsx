import { FormEvent, useState } from "react";
import { Logo } from "@/components/brand/Logo";
import { useAuth } from "../auth/AuthProvider";

type Mode = "login" | "register";

export function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const isRegister = mode === "register";

  function switchMode(next: Mode) {
    setMode(next);
    setError(null);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (isRegister) {
        await register({
          email,
          full_name: fullName,
          password,
          ...(code ? { registration_code: code } : {}),
        });
      } else {
        await login(email, password);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--bg)] px-4">
      <div className="card w-full max-w-md p-8">
        <div className="mb-6 flex justify-center">
          <Logo size="lg" withWordmark />
        </div>
        <h1 className="mb-1 text-center text-xl font-semibold">
          {isRegister ? "Create your account" : "Welcome back"}
        </h1>
        <p className="mb-6 text-center text-sm text-[var(--text-muted)]">
          {isRegister ? "Join Travel System" : "Sign in to Travel System"}
        </p>
        <form onSubmit={onSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="mb-1 block text-sm font-medium">Full name</label>
              <input
                type="text"
                className="input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                minLength={2}
                autoFocus
              />
            </div>
          )}
          <div>
            <label className="mb-1 block text-sm font-medium">Email</label>
            <input
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus={!isRegister}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Password</label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={isRegister ? 8 : undefined}
            />
          </div>
          {isRegister && (
            <div>
              <label className="mb-1 block text-sm font-medium">
                Registration code{" "}
                <span className="text-[var(--text-muted)]">(if required)</span>
              </label>
              <input
                type="text"
                className="input"
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
            </div>
          )}
          {error && (
            <p className="text-sm text-[var(--status-rejected)]">{error}</p>
          )}
          <button
            type="submit"
            className="btn-primary w-full"
            disabled={loading}
          >
            {loading
              ? isRegister
                ? "Creating account…"
                : "Signing in…"
              : isRegister
                ? "Create account"
                : "Sign in"}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-[var(--text-muted)]">
          {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
          <button
            type="button"
            className="font-medium text-[var(--primary-600)] hover:underline"
            onClick={() => switchMode(isRegister ? "login" : "register")}
          >
            {isRegister ? "Sign in" : "Create one"}
          </button>
        </p>
      </div>
    </div>
  );
}
