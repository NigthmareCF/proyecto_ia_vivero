import { useNotificationStore } from "../../store/notificationStore";

export function DashboardPage() {
  const toasts = useNotificationStore((state) => state.toasts);

  return (
    <section className="grid gap-6">
      <div className="grid gap-4 md:grid-cols-3">
        {[
          ["Patrullajes", "12 activos"],
          ["Alertas", `${toasts.length} recientes`],
          ["Robot", "Conectado"],
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
