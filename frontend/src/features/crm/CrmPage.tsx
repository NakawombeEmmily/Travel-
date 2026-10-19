import { FormEvent, useEffect, useState } from "react";
import { api } from "@/config/api";
import type { Client, ClientListResponse } from "@/features/auth/types";
import type {
  Interaction,
  InteractionListResponse,
  Tag,
  TagListResponse,
} from "@/features/types";

const TYPES = ["call", "email", "whatsapp", "meeting", "other"];

export function CrmPage() {
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [iForm, setIForm] = useState({
    client_id: "",
    interaction_type: "call",
    notes: "",
    follow_up_date: "",
  });
  const [tagForm, setTagForm] = useState({ name: "", color: "#F97316" });
  const [attach, setAttach] = useState({ client_id: "", tag_id: "" });
  const [clientTags, setClientTags] = useState<Tag[]>([]);
  const [saving, setSaving] = useState(false);

  async function load() {
    try {
      const [ints, tgs] = await Promise.all([
        api.get<InteractionListResponse>("/interactions?page=1&page_size=100"),
        api.get<TagListResponse>("/tags"),
      ]);
      setInteractions(ints.items);
      setTags(tgs.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    }
  }

  useEffect(() => {
    load();
    api
      .get<ClientListResponse>("/clients?page=1&page_size=100")
      .then((r) => setClients(r.items))
      .catch(() => setClients([]));
  }, []);

  async function loadClientTags(clientId: string) {
    setAttach((a) => ({ ...a, client_id: clientId }));
    if (!clientId) {
      setClientTags([]);
      return;
    }
    try {
      const res = await api.get<TagListResponse>(`/clients/${clientId}/tags`);
      setClientTags(res.items);
    } catch {
      setClientTags([]);
    }
  }

  async function logInteraction(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post<Interaction>("/interactions", {
        ...iForm,
        notes: iForm.notes || null,
        follow_up_date: iForm.follow_up_date || null,
      });
      setIForm({
        client_id: "",
        interaction_type: "call",
        notes: "",
        follow_up_date: "",
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  async function removeInteraction(id: string) {
    try {
      await api.delete(`/interactions/${id}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    }
  }

  async function createTag(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post<Tag>("/tags", tagForm);
      setTagForm({ name: "", color: "#F97316" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create tag");
    } finally {
      setSaving(false);
    }
  }

  async function deleteTag(id: string) {
    try {
      await api.delete(`/tags/${id}`);
      await load();
      if (attach.client_id) await loadClientTags(attach.client_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete tag");
    }
  }

  async function attachTag() {
    if (!attach.client_id || !attach.tag_id) return;
    try {
      await api.post(`/clients/${attach.client_id}/tags/${attach.tag_id}`);
      await loadClientTags(attach.client_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to attach tag");
    }
  }

  async function detachTag(tagId: string) {
    if (!attach.client_id) return;
    try {
      await api.delete(`/clients/${attach.client_id}/tags/${tagId}`);
      await loadClientTags(attach.client_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to detach tag");
    }
  }

  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">CRM</h1>

      {error && <p className="mb-3 text-sm text-[var(--status-rejected)]">{error}</p>}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="card mb-4 p-4">
            <h2 className="mb-3 font-medium">Log interaction</h2>
            <form onSubmit={logInteraction} className="grid gap-3 sm:grid-cols-2">
              <select
                className="input"
                required
                value={iForm.client_id}
                onChange={(e) => setIForm({ ...iForm, client_id: e.target.value })}
              >
                <option value="">Select a client…</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.full_name}
                  </option>
                ))}
              </select>
              <select
                className="input"
                value={iForm.interaction_type}
                onChange={(e) =>
                  setIForm({ ...iForm, interaction_type: e.target.value })
                }
              >
                {TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <input
                type="date"
                className="input"
                value={iForm.follow_up_date}
                onChange={(e) =>
                  setIForm({ ...iForm, follow_up_date: e.target.value })
                }
              />
              <input
                className="input sm:col-span-2"
                placeholder="Notes"
                value={iForm.notes}
                onChange={(e) => setIForm({ ...iForm, notes: e.target.value })}
              />
              <div className="sm:col-span-2">
                <button className="btn-primary" disabled={saving}>
                  Log
                </button>
              </div>
            </form>
          </div>

          <div className="card overflow-hidden">
            <div className="border-b border-[var(--border)] px-4 py-3 font-medium">
              Interaction log
            </div>
            <table className="w-full text-sm">
              <tbody>
                {interactions.map((i) => (
                  <tr key={i.id} className="border-t border-[var(--border)]">
                    <td className="px-4 py-3 font-medium">{i.client_name ?? "—"}</td>
                    <td className="px-4 py-3 capitalize">{i.interaction_type}</td>
                    <td className="px-4 py-3">{i.notes ?? "—"}</td>
                    <td className="px-4 py-3 text-[var(--text-muted)]">
                      {new Date(i.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        className="text-[var(--status-rejected)]"
                        onClick={() => removeInteraction(i.id)}
                      >
                        ✕
                      </button>
                    </td>
                  </tr>
                ))}
                {interactions.length === 0 && (
                  <tr>
                    <td className="px-4 py-6 text-center text-[var(--text-muted)]">
                      No interactions logged
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <div className="card mb-4 p-4">
            <h2 className="mb-3 font-medium">Tags</h2>
            <form onSubmit={createTag} className="mb-3 flex gap-2">
              <input
                className="input"
                placeholder="Tag name"
                required
                value={tagForm.name}
                onChange={(e) => setTagForm({ ...tagForm, name: e.target.value })}
              />
              <input
                type="color"
                className="h-10 w-12 rounded border border-[var(--border)]"
                value={tagForm.color}
                onChange={(e) => setTagForm({ ...tagForm, color: e.target.value })}
              />
              <button className="btn-primary" disabled={saving}>
                Add
              </button>
            </form>
            <div className="flex flex-wrap gap-2">
              {tags.map((t) => (
                <span
                  key={t.id}
                  className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs text-white"
                  style={{ backgroundColor: t.color }}
                >
                  {t.name}
                  <button onClick={() => deleteTag(t.id)}>✕</button>
                </span>
              ))}
              {tags.length === 0 && (
                <span className="text-xs text-[var(--text-muted)]">No tags</span>
              )}
            </div>
          </div>

          <div className="card p-4">
            <h2 className="mb-3 font-medium">Client tags</h2>
            <select
              className="input mb-2"
              value={attach.client_id}
              onChange={(e) => loadClientTags(e.target.value)}
            >
              <option value="">Select a client…</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.full_name}
                </option>
              ))}
            </select>
            <div className="mb-3 flex gap-2">
              <select
                className="input"
                value={attach.tag_id}
                onChange={(e) => setAttach({ ...attach, tag_id: e.target.value })}
              >
                <option value="">Select tag…</option>
                {tags.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
              <button className="btn-primary" onClick={attachTag}>
                Attach
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {clientTags.map((t) => (
                <span
                  key={t.id}
                  className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs text-white"
                  style={{ backgroundColor: t.color }}
                >
                  {t.name}
                  <button onClick={() => detachTag(t.id)}>✕</button>
                </span>
              ))}
              {attach.client_id && clientTags.length === 0 && (
                <span className="text-xs text-[var(--text-muted)]">
                  No tags on this client
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
