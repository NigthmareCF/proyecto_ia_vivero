import { normalizeRole, useAuthStore } from "../../store/authStore";

export function Navbar() {
  const { fullName, role, clear } = useAuthStore();
  const displayRole = normalizeRole(role) ?? role;

  return (
    <header className="flex items-center justify-between rounded-3xl bg-white/70 px-6 py-4 shadow-sm">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-moss">Centro operativo</p>
        <h1 className="font-display text-3xl text-ink">Monitoreo autonomo</h1>
      </div>
      <div className="text-right">
        <p className="font-semibold">{fullName ?? "Operador"}</p>
        <p className="text-sm text-moss">{displayRole ?? "Sin rol"}</p>
        <button className="mt-2 rounded-full bg-ink px-4 py-2 text-sm text-white" onClick={clear}>
          Cerrar sesion
        </button>
      </div>
    </header>
  );
}
