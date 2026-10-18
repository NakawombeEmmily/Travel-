import { useEffect, useState } from "react";
import { Logo } from "@/components/brand/Logo";
import { API_BASE, API_BASE_MISSING, api } from "@/config/api";

interface Props {
  onReady: () => void;
}

export function WakingUp({ onReady }: Props) {
  const [seconds, setSeconds] = useState(0);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let attempts = 0;
    const start = Date.now();
    const interval = setInterval(async () => {
      attempts += 1;
      setSeconds(Math.round((Date.now() - start) / 1000));
      try {
        await api.get("/health");
        if (!cancelled) {
          clearInterval(interval);
          onReady();
        }
      } catch {
        if (!cancelled && attempts >= 30) {
          clearInterval(interval);
          setFailed(true);
        }
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
  const showError = (API_BASE_MISSING || failed) && !isLocalhost;

  if (showError) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
        <Logo size="xl" withWordmark />
        <p className="text-sm font-medium text-[var(--text)]">
          Can&rsquo;t reach the server.
        </p>
        <p className="max-w-md text-xs text-[var(--text-muted)]">
          Couldn&rsquo;t reach{" "}
          <code className="rounded bg-black/5 px-1">{API_BASE}</code> after{" "}
          {seconds}s. Check that:
        </p>
        <ul className="max-w-md list-disc space-y-1 text-left text-xs text-[var(--text-muted)]">
          <li>
            Vercel&rsquo;s <code>VITE_API_BASE_URL</code> is your Render API URL
          </li>
          <li>
            Render&rsquo;s <code>CORS_ORIGINS</code> includes{" "}
            <code>{window.location.origin}</code>
          </li>
          <li>The Render API service is live (finished deploying)</li>
        </ul>
        <button
          type="button"
          className="btn-primary mt-2"
          onClick={() => window.location.reload()}
        >
          Retry
        </button>
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
