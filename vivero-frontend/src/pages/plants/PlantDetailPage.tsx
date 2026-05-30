import { Link, useParams } from "react-router-dom";

function decodePlantId(value?: string) {
  if (!value) return "Planta sin seleccionar";
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export function PlantDetailPage() {
  const { id } = useParams();
  const plantLabel = decodePlantId(id);

  return (
    <section className="space-y-6">
      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <p className="text-xs uppercase tracking-[0.18em] text-moss">Reporte general planta/maceta</p>
        <h2 className="mt-2 font-display text-3xl text-ink">{plantLabel}</h2>
        <p className="mt-3 max-w-3xl text-sm text-moss">
          Esta vista queda preparada para consolidar el historial de patrullaje, el clasificador local, el analisis Qwen y el reporte final generado al cierre del recorrido.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link to="/patrols" className="rounded-2xl bg-ink px-5 py-3 text-sm font-semibold text-white transition hover:bg-clay">
            Ver patrullajes
          </Link>
          <Link to="/analisis" className="rounded-2xl border border-sand px-5 py-3 text-sm font-semibold text-ink transition hover:border-clay">
            Analisis manual
          </Link>
        </div>
      </article>

      <div className="grid gap-4 md:grid-cols-3">
        {[
          ["Estado", "Pendiente de consolidar"],
          ["Evidencias", "Imagenes relevantes al finalizar"],
          ["Reporte", "Disponible tras cierre de patrullaje"],
        ].map(([label, value]) => (
          <article key={label} className="rounded-[1.5rem] bg-white p-5 shadow-sm">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">{label}</p>
            <p className="mt-3 text-sm font-semibold text-ink">{value}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
