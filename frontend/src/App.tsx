import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { AuthProvider, useAuth } from "@/features/auth/AuthProvider";
import { LoginPage } from "@/features/auth/LoginPage";
import { ClientsPage } from "@/features/clients/ClientsPage";
import { CrmPage } from "@/features/crm/CrmPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { FeedbackPage } from "@/features/feedback/FeedbackPage";
import { PaymentsPage } from "@/features/payments/PaymentsPage";
import { PipelinePage } from "@/features/pipeline/PipelinePage";
import { TasksPage } from "@/features/tasks/TasksPage";
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
        <Route path="/feedback" element={<FeedbackPage />} />
        <Route path="/pipeline" element={<PipelinePage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/crm" element={<CrmPage />} />
        <Route path="/payments" element={<PaymentsPage />} />
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
