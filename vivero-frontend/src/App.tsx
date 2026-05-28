import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/layout/ProtectedRoute";
import { Sidebar } from "./components/layout/Sidebar";
import { Navbar } from "./components/layout/Navbar";
import { RenderGuard } from "./components/layout/RenderGuard";
import { VoiceCommandDock } from "./components/layout/VoiceCommandDock";
import { useAuth } from "./hooks/useAuth";
import { LoginPage } from "./pages/auth/LoginPage";
import { AppRole, normalizeRole } from "./store/authStore";

const DashboardPage = lazy(() => import("./pages/dashboard/DashboardPage").then((module) => ({ default: module.DashboardPage })));
const PlantsPage = lazy(() => import("./pages/plants/PlantsPage").then((module) => ({ default: module.PlantsPage })));
const PlantDetailPage = lazy(() => import("./pages/plants/PlantDetailPage").then((module) => ({ default: module.PlantDetailPage })));
const PatrolsPage = lazy(() => import("./pages/patrols/PatrolsPage").then((module) => ({ default: module.PatrolsPage })));
const PatrolDetailPage = lazy(() => import("./pages/patrols/PatrolDetailPage").then((module) => ({ default: module.PatrolDetailPage })));
const RobotControlPage = lazy(() => import("./pages/robot/RobotControlPage").then((module) => ({ default: module.RobotControlPage })));
const GotoPlantPage = lazy(() => import("./pages/robot/GotoPlantPage").then((module) => ({ default: module.GotoPlantPage })));
const ReportsPage = lazy(() => import("./pages/reports/ReportsPage").then((module) => ({ default: module.ReportsPage })));
const AnalisisPlantaPage = lazy(() => import("./pages/analisis/AnalisisPlantaPage").then((module) => ({ default: module.AnalisisPlantaPage })));
const UsersPage = lazy(() => import("./pages/users/UsersPage").then((module) => ({ default: module.UsersPage })));

const defaultRouteByRole: Record<AppRole, string> = {
  ADMIN: "/dashboard",
  CONTROLLER: "/patrols",
  VIEWER: "/reports",
};

function hasAccess(role: AppRole, allowedRoles: AppRole[]) {
  return allowedRoles.includes(role);
}

function guardRoute(title: string, element: JSX.Element) {
  return <RenderGuard title={title}>{element}</RenderGuard>;
}

function Shell() {
  const { isAuthenticated, role } = useAuth();

  if (!isAuthenticated) {
    return <Routes><Route path="*" element={<LoginPage />} /></Routes>;
  }

  const activeRole = normalizeRole(role) ?? "VIEWER";
  const fallbackRoute = defaultRouteByRole[activeRole] ?? "/reports";

  return (
    <div className="mx-auto flex min-h-screen max-w-[1440px] gap-6 px-6 py-6">
      <Sidebar />
      <main className="flex-1 space-y-6">
        <Navbar />
        <RenderGuard title="Control por voz">
          <VoiceCommandDock />
        </RenderGuard>
        <Suspense fallback={<div className="rounded-3xl bg-white p-6 text-moss shadow-sm">Cargando modulo...</div>}>
          <Routes>
            <Route
              path="/dashboard"
              element={hasAccess(activeRole, ["ADMIN"]) ? guardRoute("Dashboard", <DashboardPage />) : <Navigate to={fallbackRoute} replace />}
            />
            <Route
              path="/plants"
              element={hasAccess(activeRole, ["ADMIN"]) ? guardRoute("Plantas", <PlantsPage />) : <Navigate to={fallbackRoute} replace />}
            />
            <Route
              path="/plants/:id"
              element={hasAccess(activeRole, ["ADMIN"]) ? guardRoute("Detalle de planta", <PlantDetailPage />) : <Navigate to={fallbackRoute} replace />}
            />
            <Route
              path="/patrols"
              element={hasAccess(activeRole, ["ADMIN", "CONTROLLER", "VIEWER"]) ? guardRoute("Patrullajes", <PatrolsPage />) : <Navigate to={fallbackRoute} replace />}
            />
            <Route
              path="/patrols/:id"
              element={hasAccess(activeRole, ["ADMIN", "CONTROLLER", "VIEWER"]) ? guardRoute("Detalle de patrullaje", <PatrolDetailPage />) : <Navigate to={fallbackRoute} replace />}
            />
            <Route
              path="/robot"
              element={hasAccess(activeRole, ["ADMIN", "CONTROLLER"]) ? guardRoute("Control del robot", <RobotControlPage />) : <Navigate to={fallbackRoute} replace />}
            />
            <Route
              path="/robot/goto"
              element={hasAccess(activeRole, ["ADMIN", "CONTROLLER"]) ? guardRoute("Ir a planta", <GotoPlantPage />) : <Navigate to={fallbackRoute} replace />}
            />
            <Route
              path="/reports"
              element={hasAccess(activeRole, ["ADMIN", "CONTROLLER", "VIEWER"]) ? guardRoute("Reportes", <ReportsPage />) : <Navigate to={fallbackRoute} replace />}
            />
            <Route
              path="/analisis"
              element={hasAccess(activeRole, ["ADMIN"]) ? guardRoute("Analisis", <AnalisisPlantaPage />) : <Navigate to={fallbackRoute} replace />}
            />
            <Route
              path="/users"
              element={hasAccess(activeRole, ["ADMIN"]) ? guardRoute("Usuarios", <UsersPage />) : <Navigate to={fallbackRoute} replace />}
            />
            <Route path="*" element={<Navigate to={fallbackRoute} replace />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}

export default function App() {
  const { isAuthenticated, role } = useAuth();
  const activeRole = normalizeRole(role) ?? "VIEWER";
  const defaultRoute = defaultRouteByRole[activeRole] ?? "/reports";

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to={defaultRoute} replace /> : <LoginPage />}
      />
      <Route element={<ProtectedRoute />}>
        <Route path="*" element={<Shell />} />
      </Route>
    </Routes>
  );
}
