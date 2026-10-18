import { useEffect, useState } from "react";
import { api } from "@/config/api";
import type { ClientListResponse } from "@/features/auth/types";

export function ClientsPage() {
  const [data, setData] = useState<ClientListResponse | null>(null);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const t = setTimeout(async () => {
      try {
        const res = await api.get<ClientListResponse>(
          `/clients?q=${encodeURIComponent(q)}&page=1&page_size=20`,
        );
        if (!cancelled) {
          setData(res);
          setError(null);
        }
      } catch (err) {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 300);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [q]);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Clients</h1>
        <span className="text-sm text-[var(--text-muted)]">
          {data ? `${data.total} total` : ""}
        </span>
      </div>

      <div className="card mb-4 p-3">
        <input
          className="input"
          placeholder="Search name, email, phone…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      {loading && (
        <p className="text-sm text-[var(--text-muted)]">Loading…</p>
      )}
      {error && <p className="text-sm text-[var(--status-rejected)]">{error}</p>}

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[var(--primary-50)] text-left text-[var(--primary-950)]">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Phone</th>
              <th className="px-4 py-3">Nationality</th>
              <th className="px-4 py-3">Passport</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((c) => (
              <tr key={c.id} className="border-t border-[var(--border)]">
                <td className="px-4 py-3 font-medium">{c.full_name}</td>
                <td className="px-4 py-3">{c.email ?? "—"}</td>
                <td className="px-4 py-3">{c.phone ?? "—"}</td>
                <td className="px-4 py-3">{c.nationality ?? "—"}</td>
                <td className="px-4 py-3">
                  <span className="font-mono">{c.passport_number_masked}</span>
                  {c.passport_expiring_soon && (
                    <span className="ml-2 rounded bg-[var(--status-pending)] px-1.5 py-0.5 text-xs text-white">
                      Expiring
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="px-4 py-8 text-center text-[var(--text-muted)]"
                >
                  No clients found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
