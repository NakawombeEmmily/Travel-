import { Logo } from "@/components/brand/Logo";

const stats = [
  { label: "Active Clients", value: "—" },
  { label: "Trips in Progress", value: "—" },
  { label: "Pending Visas", value: "—" },
  { label: "Revenue (MTD)", value: "—" },
];

export function DashboardPage() {
  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Dashboard</h1>
      <p className="mb-6 text-sm text-[var(--text-muted)]">
        Welcome to Travel System. More metrics arrive in later phases.
      </p>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <div key={s.label} className="card p-5">
            <div className="text-sm text-[var(--text-muted)]">{s.label}</div>
            <div className="mt-2 text-3xl font-semibold text-[var(--primary-600)]">
              {s.value}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-8 flex items-center gap-3 text-sm text-[var(--text-muted)]">
        <Logo size="sm" withWordmark={false} />
        <span>Phase 1 foundation complete.</span>
      </div>
    </div>
  );
}
