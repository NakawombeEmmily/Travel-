import { useEffect, useState } from "react";
import { api, downloadFile } from "@/config/api";
import type {
  AnalyticsSummary,
  CsvDataset,
  RevenueSummary,
  TrendPoint,
} from "@/features/types";

const CSV_DATASETS: CsvDataset[] = [
  "clients",
  "trips",
  "visas",
  "leads",
  "feedback",
  "payments",
];

function Bar({
  label,
  value,
  max,
  suffix,
}: {
  label: string;
  value: number;
  max: number;
  suffix?: string;
}) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="mb-2">
      <div className="flex justify-between text-sm">
        <span className="capitalize text-[var(--text-muted)]">
          {label.replace("_", " ")}
        </span>
        <span className="font-medium">
          {value}
          {suffix}
        </span>
      </div>
      <div className="mt-1 h-2 w-full rounded bg-[var(--primary-50)]">
        <div
          className="h-2 rounded bg-[var(--primary-500)]"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card p-5">
      <div className="text-sm text-[var(--text-muted)]">{label}</div>
      <div className="mt-2 text-3xl font-semibold text-[var(--primary-600)]">
        {value}
      </div>
    </div>
  );
}

export function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [revenue, setRevenue] = useState<RevenueSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [s, t, r] = await Promise.all([
          api.get<AnalyticsSummary>("/analytics/summary"),
          api.get<TrendPoint[]>("/analytics/trends?months=6"),
          api.get<RevenueSummary[]>(
            "/analytics/revenue?period_type=monthly&limit=12",
          ),
        ]);
        if (cancelled) return;
        setSummary(s);
        setTrends(t);
        setRevenue(r);
        setError(null);
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

  async function exportCsv(dataset: CsvDataset) {
    setExporting(dataset);
    setError(null);
    try {
      await downloadFile(
        `/analytics/export/${dataset}`,
        `${dataset}-export.csv`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExporting(null);
    }
  }

  const maxNationality = summary
    ? Math.max(1, ...summary.nationalities.map((n) => n.count))
    : 1;
  const maxRating = summary
    ? Math.max(1, ...Object.values(summary.ratings.distribution))
    : 1;
  const maxTrend = trends.length
    ? Math.max(1, ...trends.map((t) => Math.max(t.clients, t.leads, t.payments)))
    : 1;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">Analytics</h1>
        <div className="flex flex-wrap gap-2">
          {CSV_DATASETS.map((dataset) => (
            <button
              key={dataset}
              className="btn-secondary"
              disabled={exporting === dataset}
              onClick={() => exportCsv(dataset)}
            >
              {exporting === dataset ? "…" : `Export ${dataset}`}
            </button>
          ))}
        </div>
      </div>

      {loading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
      {error && <p className="mb-3 text-sm text-[var(--status-rejected)]">{error}</p>}

      {summary && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Active clients" value={summary.total_clients} />
            <StatCard label="Trips" value={summary.total_trips} />
            <StatCard
              label="Avg rating"
              value={`${summary.ratings.average.toFixed(1)} / 5`}
            />
            <StatCard
              label="Reviews"
              value={summary.ratings.count}
            />
            <StatCard
              label="Lead conversion"
              value={`${summary.conversion.conversion_rate}%`}
            />
            <StatCard
              label="Open leads"
              value={summary.conversion.open}
            />
            <StatCard
              label="Visa approval rate"
              value={`${summary.visas.approval_rate}%`}
            />
            <StatCard
              label="Visas decided"
              value={summary.visas.decided}
            />
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="card p-5">
              <div className="mb-3 text-sm font-medium">Rating distribution</div>
              {Object.keys(summary.ratings.distribution).length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">No reviews yet</p>
              ) : (
                Object.entries(summary.ratings.distribution)
                  .sort((a, b) => Number(b[0]) - Number(a[0]))
                  .map(([rating, count]) => (
                    <Bar
                      key={rating}
                      label={`${rating} star`}
                      value={count}
                      max={maxRating}
                    />
                  ))
              )}
            </div>

            <div className="card p-5">
              <div className="mb-3 text-sm font-medium">Client nationalities</div>
              {summary.nationalities.length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">No clients yet</p>
              ) : (
                summary.nationalities.map((item) => (
                  <Bar
                    key={item.label}
                    label={item.label}
                    value={item.count}
                    max={maxNationality}
                  />
                ))
              )}
            </div>

            <div className="card p-5">
              <div className="mb-3 text-sm font-medium">Visa pipeline</div>
              {Object.keys(summary.visas.by_status).length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">No visas yet</p>
              ) : (
                Object.entries(summary.visas.by_status).map(([status, count]) => (
                  <Bar
                    key={status}
                    label={status}
                    value={count}
                    max={summary.visas.total || 1}
                  />
                ))
              )}
            </div>

            <div className="card p-5">
              <div className="mb-3 text-sm font-medium">Lead pipeline</div>
              {Object.keys(summary.trips_by_status).length === 0 &&
              summary.conversion.total_leads === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">No leads yet</p>
              ) : (
                <ul className="space-y-1 text-sm">
                  <li className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Total leads</span>
                    <span className="font-medium">
                      {summary.conversion.total_leads}
                    </span>
                  </li>
                  <li className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Won</span>
                    <span className="font-medium">{summary.conversion.won}</span>
                  </li>
                  <li className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Lost</span>
                    <span className="font-medium">{summary.conversion.lost}</span>
                  </li>
                </ul>
              )}
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="card p-5">
              <div className="mb-3 text-sm font-medium">Revenue by currency</div>
              {summary.revenue_by_currency.length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">No payments yet</p>
              ) : (
                <ul className="space-y-1 text-sm">
                  {summary.revenue_by_currency.map((item) => (
                    <li key={item.currency} className="flex justify-between">
                      <span className="text-[var(--text-muted)]">
                        {item.currency} ({item.count} payments)
                      </span>
                      <span className="font-medium">{item.total}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="card p-5">
              <div className="mb-3 text-sm font-medium">Feedback sentiment</div>
              {Object.keys(summary.feedback_by_sentiment).length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">No feedback yet</p>
              ) : (
                Object.entries(summary.feedback_by_sentiment).map(([k, v]) => (
                  <Bar
                    key={k}
                    label={k}
                    value={v}
                    max={summary.ratings.count || 1}
                  />
                ))
              )}
            </div>
          </div>

          <div className="mt-6 card overflow-hidden">
            <div className="border-b border-[var(--border)] px-4 py-3 font-medium">
              Monthly trends (last 6 months)
            </div>
            <table className="w-full text-sm">
              <thead className="text-left text-[var(--text-muted)]">
                <tr>
                  <th className="px-4 py-2">Month</th>
                  <th className="px-4 py-2">Clients</th>
                  <th className="px-4 py-2">Leads</th>
                  <th className="px-4 py-2">Payments</th>
                  <th className="px-4 py-2">Revenue</th>
                  <th className="px-4 py-2">Feedback</th>
                </tr>
              </thead>
              <tbody>
                {trends.map((t) => (
                  <tr key={t.month} className="border-t border-[var(--border)]">
                    <td className="px-4 py-2 font-medium">{t.month}</td>
                    <td className="px-4 py-2">
                      <span className="inline-flex items-center gap-2">
                        {t.clients}
                        <span
                          className="h-2 rounded bg-[var(--primary-500)]"
                          style={{
                            width: `${Math.round((t.clients / maxTrend) * 60)}px`,
                          }}
                        />
                      </span>
                    </td>
                    <td className="px-4 py-2">{t.leads}</td>
                    <td className="px-4 py-2">{t.payments}</td>
                    <td className="px-4 py-2">{t.revenue}</td>
                    <td className="px-4 py-2">{t.feedback}</td>
                  </tr>
                ))}
                {trends.length === 0 && (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-4 py-6 text-center text-[var(--text-muted)]"
                    >
                      No trend data
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="mt-6 card overflow-hidden">
            <div className="border-b border-[var(--border)] px-4 py-3 font-medium">
              Monthly revenue summary
            </div>
            <table className="w-full text-sm">
              <thead className="bg-[var(--primary-50)] text-left text-[var(--primary-950)]">
                <tr>
                  <th className="px-4 py-3">Period</th>
                  <th className="px-4 py-3">Currency</th>
                  <th className="px-4 py-3">Total</th>
                  <th className="px-4 py-3">Transactions</th>
                  <th className="px-4 py-3">Completed</th>
                  <th className="px-4 py-3">Failed</th>
                  <th className="px-4 py-3">Refunded</th>
                </tr>
              </thead>
              <tbody>
                {revenue.map((row) => (
                  <tr
                    key={`${row.summary_date}-${row.currency}`}
                    className="border-t border-[var(--border)]"
                  >
                    <td className="px-4 py-3 font-medium">{row.summary_date}</td>
                    <td className="px-4 py-3">{row.currency}</td>
                    <td className="px-4 py-3">{row.total_amount}</td>
                    <td className="px-4 py-3">{row.transaction_count}</td>
                    <td className="px-4 py-3">{row.completed_count}</td>
                    <td className="px-4 py-3">{row.failed_count}</td>
                    <td className="px-4 py-3">{row.refunded_count}</td>
                  </tr>
                ))}
                {revenue.length === 0 && (
                  <tr>
                    <td
                      colSpan={7}
                      className="px-4 py-6 text-center text-[var(--text-muted)]"
                    >
                      No revenue summaries yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <p className="mt-4 text-xs text-[var(--text-muted)]">
            Generated {new Date(summary.generated_at).toLocaleString()}
          </p>
        </>
      )}
    </div>
  );
}
