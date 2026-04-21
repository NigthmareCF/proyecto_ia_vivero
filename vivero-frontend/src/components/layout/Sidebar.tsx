import { NavLink } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

type Role = "ADMIN" | "CONTROLLER" | "VIEWER";

const linksByRole: Record<Role, Array<[string, string]>> = {
  ADMIN: [
    ["/dashboard", "Dashboard"],
    ["/plants", "Plantas"],
    ["/patrols", "Patrullajes"],
    ["/robot", "Robot"],
    ["/reports", "Reportes"],
    ["/analisis", "Analisis"],
    ["/users", "Usuarios"],
  ],
  CONTROLLER: [
    ["/patrols", "Patrullajes"],
    ["/robot", "Robot"],
    ["/reports", "Reportes"],
  ],
  VIEWER: [
    ["/patrols", "Patrullajes"],
    ["/reports", "Reportes"],
  ],
};

export function Sidebar() {
  const { role } = useAuth();
  const activeRole = (role ?? "VIEWER") as Role;
  const links = linksByRole[activeRole] ?? linksByRole.VIEWER;

  return (
    <aside className="w-full max-w-60 rounded-3xl bg-ink p-5 text-sand shadow-xl">
      <p className="font-display text-2xl">Vivero IA</p>
      <p className="mt-2 text-sm text-sand/70">Operaciones del vivero en tiempo real</p>
      <nav className="mt-6 flex flex-col gap-2">
        {links.map(([to, label]) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `rounded-2xl px-4 py-3 text-sm transition ${isActive ? "bg-clay text-white" : "bg-white/5 hover:bg-white/10"}`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
