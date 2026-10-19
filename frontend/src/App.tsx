import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { AuthProvider, useAuth } from "@/features/auth/AuthProvider";
import { LoginPage } from "@/features/auth/LoginPage";
import { ClientsPage } from "@/features/clients/ClientsPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { TripsPage } from "@/features/trips/TripsPage";
import { VisasPage } from "@/features/visas/VisasPage";

function Protected() {
  const { user, hasToken } = useAuth();
  if (!hasToken && !user) return <Navigate to="/login" replace />;
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/clients" element={<ClientsPage />} />
        <Route path="/trips" element={<TripsPage />} />
        <Route path="/visas" element={<VisasPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}

function Root() {
  const { user, hasToken } = useAuth();
  const authed = !!user || !!hasToken;
  return (
    <Routes>
      <Route
        path="/login"
        element={authed ? <Navigate to="/" replace /> : <LoginPage />}
      />
      <Route path="/*" element={authed ? <Protected /> : <Navigate to="/login" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Root />
      </AuthProvider>
    </BrowserRouter>
  );
}
