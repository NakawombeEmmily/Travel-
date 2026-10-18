import { useEffect, useState } from "react";
import { Logo } from "@/components/brand/Logo";
import { API_BASE, API_BASE_MISSING, api } from "@/config/api";

interface Props {
  onReady: () => void;
}

export function WakingUp({ onReady }: Props) {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const start = Date.now();
    const interval = setInterval(async () => {
      setSeconds(Math.round((Date.now() - start) / 1000));
      try {
        await api.get("/health");
        if (!cancelled) {
          clearInterval(interval);
          onReady();
        }
      } catch {
        if (cancelled) clearInterval(interval);
      }
    }, 3000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [onReady]);

  const isLocalhost =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";
  const misconfigured = API_BASE_MISSING && !isLocalhost;

  if (misconfigured) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
        <Logo size="xl" withWordmark />
        <p className="text-sm font-medium text-[var(--text)]">
          API URL is not configured.
        </p>
        <p className="max-w-md text-xs text-[var(--text-muted)]">
          In Vercel → Settings → Environment Variables, set{" "}
          <code className="mx-1 rounded bg-black/5 px-1">VITE_API_BASE_URL</code>{" "}
          to your Render API URL (e.g.
          https://travel-system-api-xxxx.onrender.com), then redeploy.
        </p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <Logo size="xl" spinning withWordmark />
      <p className="text-sm text-[var(--text-muted)]">
        Waking up server… ({seconds}s)
      </p>
      <p className="text-xs text-[var(--text-muted)]">{API_BASE}</p>
    </div>
  );
}
