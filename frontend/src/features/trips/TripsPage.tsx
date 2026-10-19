import { FormEvent, useEffect, useState } from "react";
import { api } from "@/config/api";
import type { Client, ClientListResponse } from "@/features/auth/types";
import type { Trip, TripListResponse } from "@/features/types";

const STATUSES = ["inquiry", "confirmed", "in_progress", "completed", "cancelled"];
const PURPOSES = ["tourism", "business", "study", "medical", "other"];
const CURRENCIES = ["USD", "UGX", "EUR", "KES"];

const emptyForm = {
  client_id: "",
  destination_country: "",
  travel_start_date: "",
  travel_end_date: "",
  purpose: "tourism",
  total_cost: "0",
  currency: "USD",
  status: "inquiry",
};

export function TripsPage() {
  const [data, setData] = useState<TripListResponse | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ...emptyForm });
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const res = await api.get<TripListResponse>("/trips?page=1&page_size=50");
      setData(res);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load trips");
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
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post<Trip>("/trips", {
        ...form,
        travel_end_date: form.travel_end_date || null,
      });
      setForm({ ...emptyForm });
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create trip");
    } finally {
      setSaving(false);
    }
  }

  async function changeStatus(id: string, status: string) {
    try {
      await api.patch(`/trips/${id}`, { status });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update trip");
    }
  }

  async function remove(id: string) {
    if (!window.confirm("Delete this trip?")) return;
    try {
      await api.delete(`/trips/${id}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete trip");
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Trips</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-[var(--text-muted)]">
            {data ? `${data.total} total` : ""}
          </span>
          <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Cancel" : "New trip"}
          </button>
        </div>
      </div>

      {error && <p className="mb-3 text-sm text-[var(--status-rejected)]">{error}</p>}

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
            <span className="mb-1 block font-medium">Destination</span>
            <input
              className="input"
              required
              value={form.destination_country}
              onChange={(e) =>
                setForm({ ...form, destination_country: e.target.value })
              }
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Start date</span>
            <input
              type="date"
              className="input"
              required
              value={form.travel_start_date}
              onChange={(e) =>
                setForm({ ...form, travel_start_date: e.target.value })
              }
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">End date</span>
            <input
              type="date"
              className="input"
              value={form.travel_end_date}
              onChange={(e) =>
                setForm({ ...form, travel_end_date: e.target.value })
              }
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Purpose</span>
            <select
              className="input"
              value={form.purpose}
              onChange={(e) => setForm({ ...form, purpose: e.target.value })}
            >
              {PURPOSES.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Total cost</span>
            <div className="flex gap-2">
              <input
                type="number"
                step="0.01"
                min="0"
                className="input"
                value={form.total_cost}
                onChange={(e) =>
                  setForm({ ...form, total_cost: e.target.value })
                }
              />
              <select
                className="input w-24"
                value={form.currency}
                onChange={(e) => setForm({ ...form, currency: e.target.value })}
              >
                {CURRENCIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          </label>
          <div className="sm:col-span-2">
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Create trip"}
            </button>
          </div>
        </form>
      )}

      {loading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[var(--primary-50)] text-left text-[var(--primary-950)]">
            <tr>
              <th className="px-4 py-3">Client</th>
              <th className="px-4 py-3">Destination</th>
              <th className="px-4 py-3">Dates</th>
              <th className="px-4 py-3">Cost</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((t) => (
              <tr key={t.id} className="border-t border-[var(--border)]">
                <td className="px-4 py-3 font-medium">
                  {t.client_name ?? "—"}
                </td>
                <td className="px-4 py-3">{t.destination_country}</td>
                <td className="px-4 py-3">
                  {t.travel_start_date}
                  {t.travel_end_date ? ` → ${t.travel_end_date}` : ""}
                </td>
                <td className="px-4 py-3">
                  {t.currency} {t.total_cost}
                </td>
                <td className="px-4 py-3">
                  <select
                    className="input py-1"
                    value={t.status}
                    onChange={(e) => changeStatus(t.id, e.target.value)}
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    className="text-[var(--status-rejected)] underline"
                    onClick={() => remove(t.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-8 text-center text-[var(--text-muted)]"
                >
                  No trips yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
