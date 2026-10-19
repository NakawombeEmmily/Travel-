import { type ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { Logo } from "@/components/brand/Logo";
import { useAuth } from "@/features/auth/AuthProvider";
import { useTheme } from "@/features/auth/ThemeProvider";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/clients", label: "Clients" },
  { to: "/trips", label: "Trips" },
  { to: "/visas", label: "Visas" },
  { to: "/pipeline", label: "Pipeline" },
  { to: "/tasks", label: "Tasks" },
  { to: "/crm", label: "CRM" },
  { to: "/feedback", label: "Feedback" },
  { to: "/payments", label: "Payments" },
  { to: "/analytics", label: "Analytics" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-60 flex-col border-r border-[var(--border)] bg-[var(--surface-elevated)]">
        <div className="flex items-center justify-between p-4">
          <Logo size="sm" withWordmark />
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `block rounded-md px-3 py-2 text-sm font-medium ${
                  isActive
                    ? "bg-[var(--primary-500)] text-[var(--primary-950)]"
                    : "text-[var(--text-muted)] hover:bg-[var(--primary-50)]"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-[var(--border)] p-4 text-xs text-[var(--text-muted)]">
          {user?.full_name}
          <div className="mt-2 flex gap-2">
            <button onClick={toggle} className="underline">
              {theme === "dark" ? "Light" : "Dark"}
            </button>
            <button onClick={logout} className="underline">
              Sign out
            </button>
          </div>
        </div>
      </aside>
      <main className="flex-1 overflow-x-auto p-6">{children}</main>
    </div>
  );
}
