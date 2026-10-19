import { useEffect, useState } from "react";
import { api } from "@/config/api";
import type { DashboardSummary } from "@/features/types";

export function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await api.get<DashboardSummary>("/dashboard/summary");
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
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const stats = data
    ? [
        { label: "Active Clients", value: data.active_clients },
        { label: "Trips in Progress", value: data.trips_in_progress },
        { label: "Pending Visas", value: data.pending_visas },
        { label: "Open Leads", value: data.open_leads },
        { label: "Open Tasks", value: data.open_tasks },
        { label: "Overdue Tasks", value: data.overdue_tasks },
        { label: "Avg Rating", value: data.feedback_average.toFixed(1) },
        { label: "Revenue (MTD)", value: data.revenue_mtd },
      ]
    : [];

  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Dashboard</h1>

      {loading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
      {error && <p className="text-sm text-[var(--status-rejected)]">{error}</p>}

      {data && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((s) => (
              <div key={s.label} className="card p-5">
                <div className="text-sm text-[var(--text-muted)]">{s.label}</div>
                <div className="mt-2 text-3xl font-semibold text-[var(--primary-600)]">
                  {s.value}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="card flex items-center justify-between p-5">
              <span className="text-sm text-[var(--text-muted)]">
                Passports expiring (90 days)
              </span>
              <span className="text-xl font-semibold">
                {data.passports_expiring_soon}
              </span>
            </div>
            <div className="card flex items-center justify-between p-5">
              <span className="text-sm text-[var(--text-muted)]">
                Visas expiring (90 days)
              </span>
              <span className="text-xl font-semibold">
                {data.visas_expiring_soon}
              </span>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="card p-5">
              <div className="mb-3 text-sm font-medium">Feedback sentiment</div>
              {Object.keys(data.feedback_by_sentiment).length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">No feedback yet</p>
              ) : (
                <ul className="space-y-1 text-sm">
                  {Object.entries(data.feedback_by_sentiment).map(([k, v]) => (
                    <li key={k} className="flex justify-between capitalize">
                      <span className="text-[var(--text-muted)]">{k}</span>
                      <span className="font-medium">{v}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="card p-5">
              <div className="mb-3 text-sm font-medium">Lead pipeline</div>
              {Object.keys(data.leads_by_status).length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">No leads yet</p>
              ) : (
                <ul className="space-y-1 text-sm">
                  {Object.entries(data.leads_by_status).map(([k, v]) => (
                    <li key={k} className="flex justify-between capitalize">
                      <span className="text-[var(--text-muted)]">
                        {k.replace("_", " ")}
                      </span>
                      <span className="font-medium">{v}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="mt-6 card overflow-hidden">
            <div className="border-b border-[var(--border)] px-4 py-3 font-medium">
              Upcoming departures
            </div>
            <table className="w-full text-sm">
              <tbody>
                {data.upcoming_departures.map((d) => (
                  <tr
                    key={d.trip_id}
                    className="border-t border-[var(--border)]"
                  >
                    <td className="px-4 py-3 font-medium">
                      {d.client_name ?? "—"}
                    </td>
                    <td className="px-4 py-3">{d.destination_country}</td>
                    <td className="px-4 py-3">{d.travel_start_date}</td>
                    <td className="px-4 py-3 text-[var(--text-muted)]">
                      {d.status}
                    </td>
                  </tr>
                ))}
                {data.upcoming_departures.length === 0 && (
                  <tr>
                    <td className="px-4 py-6 text-center text-[var(--text-muted)]">
                      No upcoming departures
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
