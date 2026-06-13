import { useEffect, useState } from "react";
import { getReports } from "../../api/reportsApi";
import { getMe, updateProfile } from "../../api/authApi";
import { useAuthStore } from "../../store/authStore";
import { useNotificationStore } from "../../store/notificationStore";

export function DashboardPage() {
  const fullName = useAuthStore((state) => state.fullName);
  const email = useAuthStore((state) => state.email);
  const role = useAuthStore((state) => state.role);
  const setSession = useAuthStore((state) => state.setSession);
  const toasts = useNotificationStore((state) => state.toasts);
  const [reportsCount, setReportsCount] = useState<number>(0);
  const [connectedHours, setConnectedHours] = useState<number>(0);
  const [manualReports, setManualReports] = useState<number>(0);
  const [meLabel, setMeLabel] = useState<string | null>(null);
  const [profileDraft, setProfileDraft] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phoneNumber: "",
    password: "",
  });
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSaving, setProfileSaving] = useState(false);

  useEffect(() => {
    getReports()
      .then((reports) => {
        setReportsCount(Array.isArray(reports) ? reports.length : 0);
        setManualReports(
          Array.isArray(reports)
            ? reports.filter((report: any) => !report.analysisProvider || report.analysisProvider === "manual").length
            : 0
        );
      })
      .catch(() => {
        setReportsCount(0);
        setManualReports(0);
      });

    getMe()
      .then((me) => {
        setMeLabel(me.fullName ? `${me.fullName} · ${me.email}` : me.email ?? null);
        const [firstName, ...rest] = (me.fullName ?? "").split(" ");
        setProfileDraft({
          firstName: firstName ?? "",
          lastName: rest.join(" "),
          email: me.email ?? "",
          phoneNumber: me.phoneNumber ?? "",
          password: "",
        });
      })
      .catch(() => setMeLabel(null));

    const startedAt = Number(localStorage.getItem("vivero-session-started-at") ?? Date.now());
    if (!localStorage.getItem("vivero-session-started-at")) {
      localStorage.setItem("vivero-session-started-at", String(startedAt));
    }
    setConnectedHours(Math.max(0, Math.round((Date.now() - startedAt) / 3_600_000)));
  }, []);

  async function handleSaveProfile() {
    setProfileSaving(true);
    setProfileError(null);
    try {
      const updated = await updateProfile(profileDraft);
      setSession(updated);
      setMeLabel(updated.fullName ? `${updated.fullName} · ${updated.email}` : updated.email ?? null);
      setProfileDraft((current) => ({ ...current, password: "" }));
    } catch (error) {
      setProfileError("No fue posible actualizar el perfil.");
      console.error(error);
    } finally {
      setProfileSaving(false);
    }
  }

  return (
    <section className="grid gap-6">
      <div className="rounded-[2rem] bg-white p-6 shadow-sm">
        <p className="text-sm uppercase tracking-[0.18em] text-moss">Perfil</p>
        <h2 className="mt-2 font-display text-3xl">{fullName ?? meLabel ?? "Usuario activo"}</h2>
        <p className="text-moss">{email ?? "Sin correo"}</p>
        <p className="mt-3 text-sm text-ink">Rol: {role ?? "N/D"} · Conectado: {connectedHours} h</p>
      </div>
      <div className="rounded-[2rem] bg-white p-6 shadow-sm">
        <h3 className="font-display text-2xl">Editar credenciales</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <input
            className="rounded-2xl border border-ink/10 px-4 py-3"
            value={profileDraft.firstName}
            onChange={(event) => setProfileDraft((current) => ({ ...current, firstName: event.target.value }))}
            placeholder="Nombre"
          />
          <input
            className="rounded-2xl border border-ink/10 px-4 py-3"
            value={profileDraft.lastName}
            onChange={(event) => setProfileDraft((current) => ({ ...current, lastName: event.target.value }))}
            placeholder="Apellido"
          />
          <input
            className="rounded-2xl border border-ink/10 px-4 py-3"
            value={profileDraft.email}
            onChange={(event) => setProfileDraft((current) => ({ ...current, email: event.target.value }))}
            placeholder="Correo"
          />
          <input
            className="rounded-2xl border border-ink/10 px-4 py-3"
            value={profileDraft.phoneNumber}
            onChange={(event) => setProfileDraft((current) => ({ ...current, phoneNumber: event.target.value }))}
            placeholder="Telefono"
          />
          <input
            className="rounded-2xl border border-ink/10 px-4 py-3 md:col-span-2"
            type="password"
            value={profileDraft.password}
            onChange={(event) => setProfileDraft((current) => ({ ...current, password: event.target.value }))}
            placeholder="Nueva contraseña opcional"
          />
        </div>
        {profileError && <p className="mt-3 text-sm text-alert">{profileError}</p>}
        <button
          type="button"
          onClick={handleSaveProfile}
          disabled={profileSaving}
          className="mt-4 rounded-2xl bg-ink px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
        >
          {profileSaving ? "Guardando..." : "Guardar perfil"}
        </button>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {[
          ["Patrullajes", `${reportsCount} reportes`],
          ["Alertas", `${toasts.length} recientes`],
          ["Robot", "Conectado"],
          ["Manuales", `${manualReports} reportes`],
        ].map(([title, value]) => (
            <article key={title} className="rounded-[2rem] bg-white p-6 shadow-sm">
            <p className="text-sm uppercase tracking-[0.18em] text-moss">{title}</p>
            <p className="mt-3 font-display text-4xl">{value}</p>
          </article>
        ))}
      </div>
      {toasts.length > 0 && (
        <div className="rounded-[2rem] bg-alert p-6 text-white">
          <h2 className="font-display text-3xl">Alertas en vivo</h2>
          {toasts.map((toast) => (
            <p key={toast.id} className="mt-2 text-sm">{toast.title}</p>
          ))}
        </div>
      )}
    </section>
  );
}
