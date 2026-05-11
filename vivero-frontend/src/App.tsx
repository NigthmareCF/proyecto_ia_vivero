import { Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/layout/ProtectedRoute";
import { Sidebar } from "./components/layout/Sidebar";
import { Navbar } from "./components/layout/Navbar";
import { VoiceCommandDock } from "./components/layout/VoiceCommandDock";
import { useAuth } from "./hooks/useAuth";
import { LoginPage } from "./pages/auth/LoginPage";
import { DashboardPage } from "./pages/dashboard/DashboardPage";
import { PlantsPage } from "./pages/plants/PlantsPage";
import { PlantDetailPage } from "./pages/plants/PlantDetailPage";
import { PatrolsPage } from "./pages/patrols/PatrolsPage";
import { PatrolDetailPage } from "./pages/patrols/PatrolDetailPage";
import { GotoPlantPage } from "./pages/robot/GotoPlantPage";
import { ReportsPage } from "./pages/reports/ReportsPage";
import { AnalisisPlantaPage } from "./pages/analisis/AnalisisPlantaPage";
import { UsersPage } from "./pages/users/UsersPage";

function Shell() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="*" element={<LoginPage />} />
      </Routes>
    );
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-[1440px] gap-6 px-6 py-6">
      <Sidebar />
      <main className="flex-1 space-y-6">
        <Navbar />
        <VoiceCommandDock />
        <Routes>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/plants" element={<PlantsPage />} />
          <Route path="/plants/:id" element={<PlantDetailPage />} />
          <Route path="/patrols" element={<PatrolsPage />} />
          <Route path="/patrols/:id" element={<PatrolDetailPage />} />
          <Route path="/robot" element={<GotoPlantPage />} />
          <Route path="/robot/goto" element={<GotoPlantPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/analisis" element={<AnalisisPlantaPage />} />
          <Route path="/users" element={<UsersPage />} />
          <Route path="*" element={<DashboardPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="*" element={<Shell />} />
      </Route>
    </Routes>
  );
}
