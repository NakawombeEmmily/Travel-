import { FormEvent, useEffect, useState } from "react";
import { api, downloadFile } from "@/config/api";
import { useAuth } from "@/features/auth/AuthProvider";
import { ACCOUNTING_ROLES } from "@/features/auth/permissions";
import type { Client, ClientListResponse } from "@/features/auth/types";
import type {
  OutboxProcessResult,
  Payment,
  PaymentInstallment,
  PaymentListResponse,
  PaymentStats,
  ReconcileResult,
} from "@/features/types";

const METHODS = ["card", "mobile_money", "bank_transfer", "cash"];
const STATUSES = ["pending", "completed", "failed", "refunded", "partial"];

interface InstallmentDraft {
  amount: string;
  due_date: string;
}

const emptyForm = {
  client_id: "",
  amount: "",
  currency: "USD",
  method: "card",
  provider: "mock",
  notes: "",
};

export function PaymentsPage() {
  const { user } = useAuth();
  const canAccount = !!user && ACCOUNTING_ROLES.includes(user.role);

  const [data, setData] = useState<PaymentListResponse | null>(null);
  const [stats, setStats] = useState<PaymentStats | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ...emptyForm });
  const [installmentsEnabled, setInstallmentsEnabled] = useState(false);
  const [installmentDrafts, setInstallmentDrafts] = useState<InstallmentDraft[]>([
    { amount: "", due_date: "" },
    { amount: "", due_date: "" },
  ]);
  const [saving, setSaving] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  async function load() {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: "1", page_size: "100" });
      if (query) params.set("q", query);
      if (statusFilter) params.set("status", statusFilter);
      const [res, stat] = await Promise.all([
        api.get<PaymentListResponse>(`/payments?${params.toString()}`),
        api.get<PaymentStats>("/payments/stats"),
      ]);
      setData(res);
      setStats(stat);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load payments");
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
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const installments = installmentsEnabled
        ? installmentDrafts
            .filter((i) => i.amount)
            .map((i) => ({
              amount: i.amount,
              due_date: i.due_date || null,
            }))
        : [];
      await api.post<Payment>("/payments", {
        ...form,
        notes: form.notes || null,
        installments,
      });
      setForm({ ...emptyForm });
      setInstallmentsEnabled(false);
      setInstallmentDrafts([
        { amount: "", due_date: "" },
        { amount: "", due_date: "" },
      ]);
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create payment");
    } finally {
      setSaving(false);
    }
  }

  async function payInstallment(payment: Payment, item: PaymentInstallment) {
    setBusy(item.id);
    setError(null);
    try {
      await api.post(
        `/payments/${payment.id}/installments/${item.id}/pay`,
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to pay installment");
    } finally {
      setBusy(null);
    }
  }

  async function refund(payment: Payment) {
    if (!window.confirm(`Refund ${payment.currency} ${payment.amount}?`)) return;
    setBusy(payment.id);
    setError(null);
    try {
      await api.post(`/payments/${payment.id}/refund`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refund");
    } finally {
      setBusy(null);
    }
  }

  async function downloadInvoice(payment: Payment) {
    setError(null);
    try {
      await downloadFile(
        `/payments/${payment.id}/invoice`,
        `${payment.invoice_number ?? payment.id}.pdf`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to download invoice");
    }
  }

  async function processOutbox() {
    setBusy("outbox");
    setError(null);
    setNotice(null);
    try {
      const res = await api.post<OutboxProcessResult>("/payments/outbox/process");
      setNotice(
        `Outbox processed: ${res.completed} completed, ${res.failed} failed, ${res.pending} pending`,
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process outbox");
    } finally {
      setBusy(null);
    }
  }

  async function reconcile() {
    setBusy("reconcile");
    setError(null);
    setNotice(null);
    try {
      const res = await api.post<ReconcileResult>("/payments/reconcile");
      setNotice(
        `Reconciled ${res.checked} payments: ${res.created} created, ${res.updated} updated, ${res.mismatched} mismatched`,
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reconcile");
    } finally {
      setBusy(null);
    }
  }

  const statusClass: Record<string, string> = {
    completed: "bg-green-100 text-green-800",
    partial: "bg-amber-100 text-amber-800",
    pending: "bg-slate-100 text-slate-700",
    failed: "bg-red-100 text-red-800",
    refunded: "bg-purple-100 text-purple-800",
  };

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Payments</h1>
        <div className="flex gap-2">
          {canAccount && (
            <>
              <button
                className="btn-secondary"
                onClick={processOutbox}
                disabled={busy === "outbox"}
              >
                {busy === "outbox" ? "Processing…" : "Process outbox"}
              </button>
              <button
                className="btn-secondary"
                onClick={reconcile}
                disabled={busy === "reconcile"}
              >
                {busy === "reconcile" ? "Reconciling…" : "Reconcile"}
              </button>
            </>
          )}
          <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Cancel" : "New payment"}
          </button>
        </div>
      </div>

      {error && <p className="mb-3 text-sm text-[var(--status-rejected)]">{error}</p>}
      {notice && <p className="mb-3 text-sm text-[var(--primary-600)]">{notice}</p>}

      {stats && (
        <div className="mb-4 grid grid-cols-3 gap-4">
          <div className="card p-4">
            <div className="text-sm text-[var(--text-muted)]">Transactions</div>
            <div className="text-2xl font-semibold">{stats.count}</div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-[var(--text-muted)]">Collected</div>
            <div className="text-2xl font-semibold text-[var(--primary-600)]">
              {stats.total_collected}
            </div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-[var(--text-muted)]">Outstanding</div>
            <div className="text-2xl font-semibold text-amber-600">
              {stats.outstanding}
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
            <span className="mb-1 block font-medium">Amount</span>
            <input
              className="input"
              required
              type="number"
              min="0.01"
              step="0.01"
              value={form.amount}
              onChange={(e) => setForm({ ...form, amount: e.target.value })}
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Currency</span>
            <input
              className="input"
              maxLength={3}
              value={form.currency}
              onChange={(e) =>
                setForm({ ...form, currency: e.target.value.toUpperCase() })
              }
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Method</span>
            <select
              className="input"
              value={form.method}
              onChange={(e) => setForm({ ...form, method: e.target.value })}
            >
              {METHODS.map((m) => (
                <option key={m} value={m}>
                  {m.replace("_", " ")}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Provider</span>
            <select
              className="input"
              value={form.provider}
              onChange={(e) => setForm({ ...form, provider: e.target.value })}
            >
              <option value="mock">mock</option>
              <option value="flutterwave">flutterwave</option>
              <option value="stripe">stripe</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Notes</span>
            <input
              className="input"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />
          </label>

          <label className="flex items-center gap-2 text-sm sm:col-span-2">
            <input
              type="checkbox"
              checked={installmentsEnabled}
              onChange={(e) => setInstallmentsEnabled(e.target.checked)}
            />
            Pay in installments
          </label>

          {installmentsEnabled && (
            <div className="sm:col-span-2">
              <div className="mb-1 text-sm font-medium">Installment schedule</div>
              <div className="space-y-2">
                {installmentDrafts.map((draft, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      className="input"
                      type="number"
                      min="0.01"
                      step="0.01"
                      placeholder="Amount"
                      value={draft.amount}
                      onChange={(e) => {
                        const next = [...installmentDrafts];
                        next[index] = { ...draft, amount: e.target.value };
                        setInstallmentDrafts(next);
                      }}
                    />
                    <input
                      className="input"
                      type="date"
                      value={draft.due_date}
                      onChange={(e) => {
                        const next = [...installmentDrafts];
                        next[index] = { ...draft, due_date: e.target.value };
                        setInstallmentDrafts(next);
                      }}
                    />
                    {installmentDrafts.length > 1 && (
                      <button
                        type="button"
                        className="text-[var(--status-rejected)] underline"
                        onClick={() =>
                          setInstallmentDrafts(
                            installmentDrafts.filter((_, i) => i !== index),
                          )
                        }
                      >
                        Remove
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <button
                type="button"
                className="mt-2 text-sm text-[var(--primary-600)] underline"
                onClick={() =>
                  setInstallmentDrafts([
                    ...installmentDrafts,
                    { amount: "", due_date: "" },
                  ])
                }
              >
                Add installment
              </button>
            </div>
          )}

          <div className="sm:col-span-2">
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Create payment"}
            </button>
          </div>
        </form>
      )}

      <div className="mb-3 flex flex-wrap gap-2">
        <input
          className="input max-w-xs"
          placeholder="Search invoice or client…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") load();
          }}
        />
        <select
          className="input max-w-[180px]"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <button className="btn-secondary" onClick={load}>
          Filter
        </button>
      </div>

      {loading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[var(--primary-50)] text-left text-[var(--primary-950)]">
            <tr>
              <th className="px-4 py-3">Invoice</th>
              <th className="px-4 py-3">Client</th>
              <th className="px-4 py-3">Amount</th>
              <th className="px-4 py-3">Method</th>
              <th className="px-4 py-3">Provider</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((p) => (
              <tr key={p.id} className="border-t border-[var(--border)] align-top">
                <td className="px-4 py-3">
                  <div className="font-medium">{p.invoice_number ?? "—"}</div>
                  <div className="text-xs text-[var(--text-muted)]">
                    {new Date(p.created_at).toLocaleDateString()}
                  </div>
                </td>
                <td className="px-4 py-3">{p.client_name ?? "—"}</td>
                <td className="px-4 py-3">
                  {p.currency} {p.amount}
                </td>
                <td className="px-4 py-3 capitalize">
                  {p.method.replace("_", " ")}
                </td>
                <td className="px-4 py-3">{p.provider}</td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded px-2 py-0.5 text-xs capitalize ${
                      statusClass[p.status] ?? ""
                    }`}
                  >
                    {p.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex flex-col items-end gap-1">
                    {p.status === "partial" &&
                      p.installments.map((item) => (
                        <div
                          key={item.id}
                          className="flex items-center gap-2 text-xs"
                        >
                          <span>
                            {item.amount} due {item.due_date ?? "—"}
                          </span>
                          {item.status !== "paid" ? (
                            <button
                              className="text-[var(--primary-600)] underline"
                              disabled={busy === item.id}
                              onClick={() => payInstallment(p, item)}
                            >
                              {busy === item.id ? "…" : "Pay"}
                            </button>
                          ) : (
                            <span className="text-green-700">paid</span>
                          )}
                        </div>
                      ))}
                    {p.status === "completed" && (
                      <button
                        className="text-[var(--primary-600)] underline"
                        onClick={() => downloadInvoice(p)}
                      >
                        Invoice
                      </button>
                    )}
                    {canAccount && p.status === "completed" && (
                      <button
                        className="text-[var(--status-rejected)] underline"
                        disabled={busy === p.id}
                        onClick={() => refund(p)}
                      >
                        Refund
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr>
                <td
                  colSpan={7}
                  className="px-4 py-8 text-center text-[var(--text-muted)]"
                >
                  No payments yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
