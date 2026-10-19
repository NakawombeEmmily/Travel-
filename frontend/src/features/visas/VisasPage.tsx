import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { api, downloadFile } from "@/config/api";
import type { Client, ClientListResponse } from "@/features/auth/types";
import type {
  DocumentItem,
  DocumentListResponse,
  Visa,
  VisaDetail,
  VisaListResponse,
  VisaStatus,
} from "@/features/types";

const COLUMNS: { key: VisaStatus; label: string }[] = [
  { key: "not_required", label: "Not required" },
  { key: "not_started", label: "Not started" },
  { key: "documents_pending", label: "Docs pending" },
  { key: "submitted", label: "Submitted" },
  { key: "in_review", label: "In review" },
  { key: "approved", label: "Approved" },
  { key: "rejected", label: "Rejected" },
  { key: "expired", label: "Expired" },
];

const emptyForm = {
  client_id: "",
  destination_country: "",
  visa_type: "",
  status: "not_started",
};

function label(value: string): string {
  return COLUMNS.find((c) => c.key === value)?.label ?? value;
}

export function VisasPage() {
  const [visas, setVisas] = useState<Visa[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ...emptyForm });
  const [saving, setSaving] = useState(false);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<VisaDetail | null>(null);
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [busy, setBusy] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const res = await api.get<VisaListResponse>("/visas?page=1&page_size=200");
      setVisas(res.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load visas");
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

  async function openDetail(id: string) {
    setSelectedId(id);
    setDetail(null);
    setDocs([]);
    try {
      const [d, dl] = await Promise.all([
        api.get<VisaDetail>(`/visas/${id}`),
        api.get<DocumentListResponse>(`/documents?visa_id=${id}`),
      ]);
      setDetail(d);
      setDocs(dl.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load visa");
    }
  }

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post<Visa>("/visas", form);
      setForm({ ...emptyForm });
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create visa");
    } finally {
      setSaving(false);
    }
  }

  async function changeStatus(status: string) {
    if (!selectedId) return;
    setBusy(true);
    try {
      await api.patch(`/visas/${selectedId}`, { status });
      await openDetail(selectedId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update visa");
    } finally {
      setBusy(false);
    }
  }

  async function uploadDoc(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !selectedId) return;
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("visa_id", selectedId);
      await api.upload("/documents", fd);
      await openDetail(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  }

  async function removeDoc(id: string) {
    try {
      await api.delete(`/documents/${id}`);
      if (selectedId) await openDetail(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Visas</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-[var(--text-muted)]">
            {visas.length} total
          </span>
          <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Cancel" : "New visa"}
          </button>
        </div>
      </div>

      {error && <p className="mb-3 text-sm text-[var(--status-rejected)]">{error}</p>}

      {showForm && (
        <form onSubmit={onCreate} className="card mb-4 grid gap-3 p-4 sm:grid-cols-3">
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
            <span className="mb-1 block font-medium">Visa type</span>
            <input
              className="input"
              value={form.visa_type}
              onChange={(e) => setForm({ ...form, visa_type: e.target.value })}
            />
          </label>
          <div className="sm:col-span-3">
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Create visa"}
            </button>
          </div>
        </form>
      )}

      {loading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}

      <div className="flex gap-3 overflow-x-auto pb-4">
        {COLUMNS.map((col) => {
          const items = visas.filter((v) => v.status === col.key);
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
                {items.map((v) => (
                  <button
                    key={v.id}
                    onClick={() => openDetail(v.id)}
                    className="w-full rounded-md border border-[var(--border)] bg-[var(--bg)] p-3 text-left text-sm hover:border-[var(--primary-500)]"
                  >
                    <div className="font-medium">
                      {v.client_name ?? "Unknown client"}
                    </div>
                    <div className="text-[var(--text-muted)]">
                      {v.destination_country}
                    </div>
                    {v.visa_type && (
                      <div className="text-xs text-[var(--text-muted)]">
                        {v.visa_type}
                      </div>
                    )}
                  </button>
                ))}
                {items.length === 0 && (
                  <p className="px-1 py-2 text-xs text-[var(--text-muted)]">
                    Empty
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {selectedId && (
        <div className="fixed inset-0 z-40 flex justify-end bg-black/40">
          <div className="h-full w-full max-w-md overflow-y-auto bg-[var(--surface-elevated)] p-5 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Visa details</h2>
              <button
                className="text-sm underline"
                onClick={() => {
                  setSelectedId(null);
                  setDetail(null);
                }}
              >
                Close
              </button>
            </div>

            {!detail && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}

            {detail && (
              <div className="space-y-5 text-sm">
                <div className="space-y-1">
                  <div>
                    <span className="text-[var(--text-muted)]">Client: </span>
                    {detail.client_name ?? "—"}
                  </div>
                  <div>
                    <span className="text-[var(--text-muted)]">Destination: </span>
                    {detail.destination_country}
                  </div>
                  <div>
                    <span className="text-[var(--text-muted)]">Type: </span>
                    {detail.visa_type ?? "—"}
                  </div>
                  <div>
                    <span className="text-[var(--text-muted)]">Reference: </span>
                    {detail.reference_number ?? "—"}
                  </div>
                  <div>
                    <span className="text-[var(--text-muted)]">Expiry: </span>
                    {detail.expiry_date ?? "—"}
                  </div>
                </div>

                <label className="block">
                  <span className="mb-1 block font-medium">Status</span>
                  <select
                    className="input"
                    value={detail.status}
                    disabled={busy}
                    onChange={(e) => changeStatus(e.target.value)}
                  >
                    {COLUMNS.map((c) => (
                      <option key={c.key} value={c.key}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </label>

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <span className="font-medium">Documents</span>
                    <label className="cursor-pointer text-xs underline">
                      {busy ? "Working…" : "Upload"}
                      <input
                        type="file"
                        className="hidden"
                        onChange={uploadDoc}
                        disabled={busy}
                      />
                    </label>
                  </div>
                  <ul className="space-y-1">
                    {docs.map((d) => (
                      <li
                        key={d.id}
                        className="flex items-center justify-between rounded border border-[var(--border)] px-2 py-1"
                      >
                        <button
                          className="truncate text-left underline"
                          onClick={() =>
                            downloadFile(
                              `/documents/${d.id}/download`,
                              d.original_filename,
                            )
                          }
                        >
                          {d.original_filename}
                        </button>
                        <button
                          className="ml-2 text-[var(--status-rejected)]"
                          onClick={() => removeDoc(d.id)}
                        >
                          ✕
                        </button>
                      </li>
                    ))}
                    {docs.length === 0 && (
                      <li className="text-xs text-[var(--text-muted)]">
                        No documents
                      </li>
                    )}
                  </ul>
                </div>

                <div>
                  <div className="mb-2 font-medium">History</div>
                  <ol className="space-y-1">
                    {detail.history.map((h) => (
                      <li key={h.id} className="text-xs text-[var(--text-muted)]">
                        {new Date(h.changed_at).toLocaleString()} —{" "}
                        {h.old_status ? `${label(h.old_status)} → ` : ""}
                        <span className="font-medium text-[var(--text)]">
                          {label(h.new_status)}
                        </span>
                      </li>
                    ))}
                    {detail.history.length === 0 && (
                      <li className="text-xs text-[var(--text-muted)]">
                        No status changes yet
                      </li>
                    )}
                  </ol>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
