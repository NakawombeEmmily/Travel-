import type { UserRole } from "./types";

export const ADMIN_ROLES: readonly UserRole[] = ["super_admin", "admin"];
export const ACCOUNTING_ROLES: readonly UserRole[] = [
  ...ADMIN_ROLES,
  "accountant",
];

export function hasRole(
  role: UserRole | null | undefined,
  allowed: readonly UserRole[],
): boolean {
  return !!role && allowed.includes(role);
}

export function canAccessPayments(role?: UserRole | null): boolean {
  return hasRole(role, ACCOUNTING_ROLES);
}

export function canAccessAnalytics(role?: UserRole | null): boolean {
  return hasRole(role, ADMIN_ROLES);
}

export function canManageUsers(role?: UserRole | null): boolean {
  return hasRole(role, ADMIN_ROLES);
}

export interface NavItem {
  to: string;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
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
  { to: "/team", label: "Team" },
];

export function navItemsFor(role?: UserRole | null): NavItem[] {
  return NAV_ITEMS.filter((item) => {
    if (item.to === "/payments") return canAccessPayments(role);
    if (item.to === "/analytics") return canAccessAnalytics(role);
    if (item.to === "/team") return canManageUsers(role);
    return true;
  });
}
