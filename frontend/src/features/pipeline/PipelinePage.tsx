import { FormEvent, useEffect, useState } from "react";
import { api } from "@/config/api";
import type { Lead, LeadListResponse } from "@/features/types";

const COLUMNS: { key: string; label: string }[] = [
  { key: "lead", label: "Lead" },
  { key: "contacted", label: "Contacted" },
  { key: "quote_sent", label: "Quote sent" },
  { key: "negotiation", label: "Negotiation" },
  { key: "won", label: "Won" },
  { key: "lost", label: "Lost" },
];

const emptyForm = {
  full_name: "",
  email: "",
  phone: "",
  source: "",
  status: "lead",
};

export function PipelinePage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ...emptyForm });
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const res = await api.get<LeadListResponse>("/leads?page=1&page_size=200");
      setLeads(res.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post<Lead>("/leads", form);
      setForm({ ...emptyForm });
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create lead");
    } finally {
      setSaving(false);
    }
  }

  async function move(id: string, status: string) {
    try {
      await api.patch(`/leads/${id}`, { status });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update lead");
    }
  }

  async function remove(id: string) {
    if (!window.confirm("Delete this lead?")) return;
    try {
      await api.delete(`/leads/${id}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete lead");
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Pipeline</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-[var(--text-muted)]">{leads.length} leads</span>
          <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Cancel" : "New lead"}
          </button>
        </div>
      </div>

      {error && <p className="mb-3 text-sm text-[var(--status-rejected)]">{error}</p>}

      {showForm && (
        <form onSubmit={onCreate} className="card mb-4 grid gap-3 p-4 sm:grid-cols-3">
          <label className="text-sm">
            <span className="mb-1 block font-medium">Full name</span>
            <input
              className="input"
              required
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Email</span>
            <input
              type="email"
              className="input"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Phone</span>
            <input
              className="input"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Source</span>
            <input
              className="input"
              placeholder="referral, website, walk-in…"
              value={form.source}
              onChange={(e) => setForm({ ...form, source: e.target.value })}
            />
          </label>
          <div className="sm:col-span-3">
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Create lead"}
            </button>
          </div>
        </form>
      )}

      {loading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}

      <div className="flex gap-3 overflow-x-auto pb-4">
        {COLUMNS.map((col) => {
          const items = leads.filter((l) => l.status === col.key);
          return (
            <div
              key={col.key}
              className="w-56 flex-shrink-0 rounded-lg border border-[var(--border)] bg-[var(--surface-elevated)]"
            >
              <div className="flex items-center justify-between border-b border-[var(--border)] px-3 py-2 text-sm font-semibold">
                <span>{col.label}</span>
                <span className="text-[var(--text-muted)]">{items.length}</span>
              </div>
              <div className="space-y-2 p-2">
                {items.map((l) => (
                  <div
                    key={l.id}
                    className="rounded-md border border-[var(--border)] bg-[var(--bg)] p-3 text-sm"
                  >
                    <div className="font-medium">{l.full_name}</div>
                    {l.email && (
                      <div className="truncate text-[var(--text-muted)]">
                        {l.email}
                      </div>
                    )}
                    {l.source && (
                      <div className="text-xs text-[var(--text-muted)]">
                        via {l.source}
                      </div>
                    )}
                    <div className="mt-2 flex items-center gap-2">
                      <select
                        className="input py-1 text-xs"
                        value={l.status}
                        onChange={(e) => move(l.id, e.target.value)}
                      >
                        {COLUMNS.map((c) => (
                          <option key={c.key} value={c.key}>
                            {c.label}
                          </option>
                        ))}
                      </select>
                      <button
                        className="text-xs text-[var(--status-rejected)]"
                        onClick={() => remove(l.id)}
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                ))}
                {items.length === 0 && (
                  <p className="px-1 py-2 text-xs text-[var(--text-muted)]">Empty</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
