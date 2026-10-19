import { FormEvent, useEffect, useState } from "react";
import { api } from "@/config/api";
import type { Client, ClientListResponse } from "@/features/auth/types";
import type {
  Feedback,
  FeedbackListResponse,
  FeedbackStats,
} from "@/features/types";

const CATEGORIES = ["service", "price", "visa_support", "communication"];
const SENTIMENTS = ["positive", "neutral", "negative", "mixed"];

const sentimentClass: Record<string, string> = {
  positive: "bg-emerald-100 text-emerald-800",
  neutral: "bg-slate-100 text-slate-700",
  negative: "bg-red-100 text-red-800",
  mixed: "bg-amber-100 text-amber-800",
};

const emptyForm = {
  client_id: "",
  rating: 5,
  category: "service",
  comment: "",
};

export function FeedbackPage() {
  const [data, setData] = useState<FeedbackListResponse | null>(null);
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [sentiment, setSentiment] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ...emptyForm });
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const query = sentiment ? `?sentiment=${sentiment}` : "";
      const [res, stat] = await Promise.all([
        api.get<FeedbackListResponse>(`/feedback${query}`),
        api.get<FeedbackStats>("/feedback/stats"),
      ]);
      setData(res);
      setStats(stat);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    api
      .get<ClientListResponse>("/clients?page=1&page_size=100")
      .then((r) => setClients(r.items))
      .catch(() => setClients([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sentiment]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post<Feedback>("/feedback", {
        ...form,
        comment: form.comment || null,
      });
      setForm({ ...emptyForm });
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  async function remove(id: string) {
    if (!window.confirm("Delete this feedback?")) return;
    try {
      await api.delete(`/feedback/${id}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Feedback</h1>
        <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancel" : "New feedback"}
        </button>
      </div>

      {error && <p className="mb-3 text-sm text-[var(--status-rejected)]">{error}</p>}

      {stats && (
        <div className="mb-4 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <div className="card p-4">
            <div className="text-sm text-[var(--text-muted)]">Responses</div>
            <div className="text-2xl font-semibold">{stats.count}</div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-[var(--text-muted)]">Avg rating</div>
            <div className="text-2xl font-semibold text-[var(--primary-600)]">
              {stats.average_rating.toFixed(1)}
            </div>
          </div>
          {SENTIMENTS.slice(0, 3).map((s) => (
            <div key={s} className="card p-4">
              <div className="text-sm text-[var(--text-muted)] capitalize">{s}</div>
              <div className="text-2xl font-semibold">
                {stats.by_sentiment[s] ?? 0}
              </div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <form onSubmit={onCreate} className="card mb-4 grid gap-3 p-4 sm:grid-cols-2">
          <label className="text-sm">
            <span className="mb-1 block font-medium">Client</span>
            <select
              className="input"
              required
              value={form.client_id}
              onChange={(e) => setForm({ ...form, client_id: e.target.value })}
            >
              <option value="">Select a client…</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.full_name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Rating</span>
            <select
              className="input"
              value={form.rating}
              onChange={(e) =>
                setForm({ ...form, rating: Number(e.target.value) })
              }
            >
              {[5, 4, 3, 2, 1].map((r) => (
                <option key={r} value={r}>
                  {r} ★
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Category</span>
            <select
              className="input"
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c.replace("_", " ")}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm sm:col-span-2">
            <span className="mb-1 block font-medium">Comment</span>
            <textarea
              className="input"
              rows={3}
              value={form.comment}
              onChange={(e) => setForm({ ...form, comment: e.target.value })}
            />
          </label>
          <div className="sm:col-span-2">
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Save feedback"}
            </button>
          </div>
        </form>
      )}

      <div className="mb-3 flex gap-2">
        <button
          className={`rounded px-3 py-1 text-sm ${sentiment === "" ? "bg-[var(--primary-500)] text-white" : "border border-[var(--border)]"}`}
          onClick={() => setSentiment("")}
        >
          All
        </button>
        {SENTIMENTS.map((s) => (
          <button
            key={s}
            className={`rounded px-3 py-1 text-sm capitalize ${sentiment === s ? "bg-[var(--primary-500)] text-white" : "border border-[var(--border)]"}`}
            onClick={() => setSentiment(s)}
          >
            {s}
          </button>
        ))}
      </div>

      {loading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[var(--primary-50)] text-left text-[var(--primary-950)]">
            <tr>
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Client</th>
              <th className="px-4 py-3">Rating</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Sentiment</th>
              <th className="px-4 py-3">Comment</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((f) => (
              <tr key={f.id} className="border-t border-[var(--border)]">
                <td className="px-4 py-3">{f.feedback_date}</td>
                <td className="px-4 py-3 font-medium">{f.client_name ?? "—"}</td>
                <td className="px-4 py-3 text-[var(--primary-600)]">
                  {"★".repeat(f.rating)}
                  <span className="text-[var(--text-muted)]">
                    {"★".repeat(5 - f.rating)}
                  </span>
                </td>
                <td className="px-4 py-3">{f.category?.replace("_", " ") ?? "—"}</td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded px-2 py-0.5 text-xs capitalize ${sentimentClass[f.sentiment] ?? ""}`}
                  >
                    {f.sentiment}
                  </span>
                </td>
                <td className="max-w-xs truncate px-4 py-3" title={f.comment ?? ""}>
                  {f.comment ?? "—"}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    className="text-[var(--status-rejected)] underline"
                    onClick={() => remove(f.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr>
                <td
                  colSpan={7}
                  className="px-4 py-8 text-center text-[var(--text-muted)]"
                >
                  No feedback yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
