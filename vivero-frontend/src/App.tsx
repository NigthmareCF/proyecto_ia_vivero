import { Navigate, Route, Routes } from "react-router-dom";
import { Sidebar } from "./components/layout/Sidebar";
import { Navbar } from "./components/layout/Navbar";
import { useAuth } from "./hooks/useAuth";
import { LoginPage } from "./pages/auth/LoginPage";
import { DashboardPage } from "./pages/dashboard/DashboardPage";
import { PlantsPage } from "./pages/plants/PlantsPage";
import { PlantDetailPage } from "./pages/plants/PlantDetailPage";
import { PatrolsPage } from "./pages/patrols/PatrolsPage";
import { PatrolDetailPage } from "./pages/patrols/PatrolDetailPage";
import { RobotControlPage } from "./pages/robot/RobotControlPage";
import { GotoPlantPage } from "./pages/robot/GotoPlantPage";
import { ReportsPage } from "./pages/reports/ReportsPage";
import { AnalisisPlantaPage } from "./pages/analisis/AnalisisPlantaPage";
import { UsersPage } from "./pages/users/UsersPage";

type Role = "ADMIN" | "CONTROLLER" | "VIEWER";

const defaultRouteByRole: Record<Role, string> = {
  ADMIN: "/dashboard",
  CONTROLLER: "/patrols",
  VIEWER: "/reports",
};

function hasAccess(role: Role, allowedRoles: Role[]) {
  return allowedRoles.includes(role);
}

function normalizeRole(role: string | null): Role {
  if (role === "ADMIN" || role === "CONTROLLER" || role === "VIEWER") {
    return role;
  }
  return "VIEWER";
}

function Shell() {
  const { role } = useAuth();

  const activeRole = normalizeRole(role);
  const fallbackRoute = defaultRouteByRole[activeRole] ?? "/reports";

  return (
    <div className="mx-auto flex min-h-screen max-w-[1440px] gap-6 px-6 py-6">
      <Sidebar />
      <main className="flex-1 space-y-6">
        <Navbar />
        <Routes>
          <Route
            path="/dashboard"
            element={hasAccess(activeRole, ["ADMIN"]) ? <DashboardPage /> : <Navigate to={fallbackRoute} replace />}
          />
          <Route
            path="/plants"
            element={hasAccess(activeRole, ["ADMIN"]) ? <PlantsPage /> : <Navigate to={fallbackRoute} replace />}
          />
          <Route
            path="/plants/:id"
            element={hasAccess(activeRole, ["ADMIN"]) ? <PlantDetailPage /> : <Navigate to={fallbackRoute} replace />}
          />
          <Route
            path="/patrols"
            element={hasAccess(activeRole, ["ADMIN", "CONTROLLER", "VIEWER"]) ? <PatrolsPage /> : <Navigate to={fallbackRoute} replace />}
          />
          <Route
            path="/patrols/:id"
            element={hasAccess(activeRole, ["ADMIN", "CONTROLLER", "VIEWER"]) ? <PatrolDetailPage /> : <Navigate to={fallbackRoute} replace />}
          />
          <Route
            path="/robot"
            element={hasAccess(activeRole, ["ADMIN", "CONTROLLER"]) ? <RobotControlPage /> : <Navigate to={fallbackRoute} replace />}
          />
          <Route
            path="/robot/goto"
            element={hasAccess(activeRole, ["ADMIN", "CONTROLLER"]) ? <GotoPlantPage /> : <Navigate to={fallbackRoute} replace />}
          />
          <Route
            path="/reports"
            element={hasAccess(activeRole, ["ADMIN", "CONTROLLER", "VIEWER"]) ? <ReportsPage /> : <Navigate to={fallbackRoute} replace />}
          />
          <Route
            path="/analisis"
            element={hasAccess(activeRole, ["ADMIN"]) ? <AnalisisPlantaPage /> : <Navigate to={fallbackRoute} replace />}
          />
          <Route
            path="/users"
            element={hasAccess(activeRole, ["ADMIN"]) ? <UsersPage /> : <Navigate to={fallbackRoute} replace />}
          />
          <Route path="*" element={<Navigate to={fallbackRoute} replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <Routes>
      <Route path="*" element={<Shell />} />
    </Routes>
  );
}
