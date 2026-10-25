import { useEffect, useState } from "react";
import { api } from "@/config/api";
import { useAuth } from "@/features/auth/AuthProvider";
import type { UserRole } from "@/features/auth/types";

interface TeamUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  last_login_at?: string | null;
  created_at: string;
}

const ALL_ROLES: UserRole[] = [
  "super_admin",
  "admin",
  "agent",
  "accountant",
  "read_only",
];

const ROLE_LABELS: Record<UserRole, string> = {
  super_admin: "Super admin",
  admin: "Admin",
  agent: "Agent",
  accountant: "Accountant",
  read_only: "Read only",
};

export function TeamPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState<TeamUser[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .get<TeamUser[]>("/users")
      .then((data) => {
        if (!cancelled) {
          setUsers(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Failed to load team");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const assignableRoles: UserRole[] =
    user?.role === "super_admin"
      ? ALL_ROLES
      : ALL_ROLES.filter((role) => role !== "super_admin");

  function canEdit(target: TeamUser): boolean {
    if (!user || target.id === user.id) return false;
    if (target.role === "super_admin" && user.role !== "super_admin") {
      return false;
    }
    return true;
  }

  async function updateRole(target: TeamUser, role: UserRole) {
    if (role === target.role) return;
    setSavingId(target.id);
    setError(null);
    try {
      const updated = await api.patch<TeamUser>(
        `/users/${target.id}/role`,
        { role },
      );
      setUsers((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update role");
    } finally {
      setSavingId(null);
    }
  }

  const needle = query.trim().toLowerCase();
  const visibleUsers = needle
    ? users.filter((item) =>
        `${item.full_name} ${item.email}`.toLowerCase().includes(needle),
      )
    : users;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Team</h1>
        <span className="text-sm text-[var(--text-muted)]">
          {users.length} {users.length === 1 ? "member" : "members"}
        </span>
      </div>

      <p className="mb-4 text-sm text-[var(--text-muted)]">
        Admins can assign roles, including promoting another team member to
        admin. Only a super admin can change a super admin or assign the super
        admin role.
      </p>

      <div className="card mb-4 p-3">
        <input
          className="input"
          placeholder="Search name or email…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </div>

      {error && <p className="mb-3 text-sm text-[var(--status-rejected)]">{error}</p>}
      {loading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[var(--primary-50)] text-left text-[var(--primary-950)]">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Last login</th>
            </tr>
          </thead>
          <tbody>
            {visibleUsers.map((member) => (
              <tr key={member.id} className="border-t border-[var(--border)]">
                <td className="px-4 py-3 font-medium">
                  {member.full_name}
                  {member.id === user?.id && (
                    <span className="ml-2 rounded bg-[var(--primary-50)] px-1.5 py-0.5 text-xs text-[var(--primary-950)]">
                      You
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">{member.email}</td>
                <td className="px-4 py-3">
                  {canEdit(member) ? (
                    <select
                      className="input py-1"
                      value={member.role}
                      disabled={savingId === member.id}
                      onChange={(event) =>
                        void updateRole(
                          member,
                          event.target.value as UserRole,
                        )
                      }
                    >
                      {assignableRoles.map((role) => (
                        <option key={role} value={role}>
                          {ROLE_LABELS[role]}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <span>{ROLE_LABELS[member.role]}</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded px-2 py-0.5 text-xs ${
                      member.is_active
                        ? "bg-green-100 text-green-800"
                        : "bg-slate-100 text-slate-700"
                    }`}
                  >
                    {member.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="px-4 py-3 text-[var(--text-muted)]">
                  {member.last_login_at
                    ? new Date(member.last_login_at).toLocaleString()
                    : "Never"}
                </td>
              </tr>
            ))}
            {!loading && visibleUsers.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="px-4 py-8 text-center text-[var(--text-muted)]"
                >
                  No team members found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
