import { FormEvent, useEffect, useState } from "react";
import { api } from "@/config/api";
import type { Client, ClientListResponse } from "@/features/auth/types";
import type { Task, TaskListResponse, TaskStats } from "@/features/types";

const STATUSES = ["pending", "in_progress", "completed", "cancelled"];
const PRIORITIES = ["low", "medium", "high"];

const emptyForm = {
  client_id: "",
  title: "",
  description: "",
  due_date: "",
  priority: "medium",
};

export function TasksPage() {
  const [data, setData] = useState<TaskListResponse | null>(null);
  const [stats, setStats] = useState<TaskStats | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ...emptyForm });
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [res, stat] = await Promise.all([
        api.get<TaskListResponse>("/tasks?page=1&page_size=100"),
        api.get<TaskStats>("/tasks/stats"),
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
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post<Task>("/tasks", {
        ...form,
        description: form.description || null,
        due_date: form.due_date || null,
      });
      setForm({ ...emptyForm });
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task");
    } finally {
      setSaving(false);
    }
  }

  async function changeStatus(id: string, status: string) {
    try {
      await api.patch(`/tasks/${id}`, { status });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update task");
    }
  }

  async function remove(id: string) {
    if (!window.confirm("Delete this task?")) return;
    try {
      await api.delete(`/tasks/${id}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete task");
    }
  }

  const priorityClass: Record<string, string> = {
    high: "bg-red-100 text-red-800",
    medium: "bg-amber-100 text-amber-800",
    low: "bg-slate-100 text-slate-700",
  };

  const today = new Date().toISOString().slice(0, 10);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Follow-up tasks</h1>
        <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancel" : "New task"}
        </button>
      </div>

      {error && <p className="mb-3 text-sm text-[var(--status-rejected)]">{error}</p>}

      {stats && (
        <div className="mb-4 grid grid-cols-3 gap-4">
          <div className="card p-4">
            <div className="text-sm text-[var(--text-muted)]">Open</div>
            <div className="text-2xl font-semibold">{stats.open}</div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-[var(--text-muted)]">Overdue</div>
            <div className="text-2xl font-semibold text-[var(--status-rejected)]">
              {stats.overdue}
            </div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-[var(--text-muted)]">Due in 7 days</div>
            <div className="text-2xl font-semibold text-[var(--primary-600)]">
              {stats.due_soon}
            </div>
          </div>
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
            <span className="mb-1 block font-medium">Title</span>
            <input
              className="input"
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Due date</span>
            <input
              type="date"
              className="input"
              value={form.due_date}
              onChange={(e) => setForm({ ...form, due_date: e.target.value })}
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Priority</span>
            <select
              className="input"
              value={form.priority}
              onChange={(e) => setForm({ ...form, priority: e.target.value })}
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm sm:col-span-2">
            <span className="mb-1 block font-medium">Description</span>
            <textarea
              className="input"
              rows={2}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </label>
          <div className="sm:col-span-2">
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Create task"}
            </button>
          </div>
        </form>
      )}

      {loading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[var(--primary-50)] text-left text-[var(--primary-950)]">
            <tr>
              <th className="px-4 py-3">Task</th>
              <th className="px-4 py-3">Client</th>
              <th className="px-4 py-3">Due</th>
              <th className="px-4 py-3">Priority</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((t) => {
              const overdue =
                t.due_date &&
                t.due_date < today &&
                t.status !== "completed" &&
                t.status !== "cancelled";
              return (
                <tr key={t.id} className="border-t border-[var(--border)]">
                  <td className="px-4 py-3">
                    <div className="font-medium">{t.title}</div>
                    {t.description && (
                      <div className="text-xs text-[var(--text-muted)]">
                        {t.description}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">{t.client_name ?? "—"}</td>
                  <td
                    className={`px-4 py-3 ${overdue ? "font-semibold text-[var(--status-rejected)]" : ""}`}
                  >
                    {t.due_date ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded px-2 py-0.5 text-xs capitalize ${priorityClass[t.priority] ?? ""}`}
                    >
                      {t.priority}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      className="input py-1"
                      value={t.status}
                      onChange={(e) => changeStatus(t.id, e.target.value)}
                    >
                      {STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {s.replace("_", " ")}
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
              );
            })}
            {data && data.items.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-8 text-center text-[var(--text-muted)]"
                >
                  No tasks yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
