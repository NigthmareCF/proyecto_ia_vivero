import { useEffect, useState } from "react";
import { getPatrolAnalysis, type PatrolAnalysisResponse } from "../../api/patrolsApi";
import { useParams } from "react-router-dom";

function stateTone(state: string) {
  switch (state) {
    case "PELIGRO":
      return "bg-rose-100 text-rose-700";
    case "ATENCION":
      return "bg-amber-100 text-amber-700";
    case "SANO":
      return "bg-emerald-100 text-emerald-700";
    default:
      return "bg-slate-100 text-slate-700";
  }
}

function absoluteImageUrl(imageUrl: string) {
  if (/^https?:\/\//i.test(imageUrl)) {
    return imageUrl;
  }
  const apiUrl = (import.meta.env.VITE_API_URL ?? "http://localhost:8080/api").replace(/\/+$/, "");
  const origin = apiUrl.endsWith("/api") ? apiUrl.slice(0, -4) : apiUrl;
  return `${origin}${imageUrl.startsWith("/") ? imageUrl : `/${imageUrl}`}`;
}

export function PatrolDetailPage() {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState<PatrolAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) {
      setError("No se encontro el patrullaje solicitado.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    getPatrolAnalysis(id)
      .then(setAnalysis)
      .catch(() => setError("No fue posible cargar el analisis consolidado del patrullaje."))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <section className="rounded-[2rem] bg-white p-6 shadow-sm text-moss">Cargando analisis del patrullaje...</section>;
  }

  if (error || !analysis) {
    return <section className="rounded-[2rem] bg-white p-6 shadow-sm text-alert">{error ?? "Sin datos disponibles."}</section>;
  }

  return (
    <section className="space-y-6">
      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="font-display text-3xl text-ink">Patrullaje {analysis.patrolId}</h2>
            <p className="mt-2 text-sm text-moss">Consolidado de estados y evidencia visual capturada por el robot.</p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-5">
            <div className="rounded-2xl bg-sand px-4 py-3"><span className="block text-moss">Grupos</span><strong>{analysis.totalGroups}</strong></div>
            <div className="rounded-2xl bg-sand px-4 py-3"><span className="block text-moss">Sanos</span><strong>{analysis.healthyCount}</strong></div>
            <div className="rounded-2xl bg-sand px-4 py-3"><span className="block text-moss">Atencion</span><strong>{analysis.attentionCount}</strong></div>
            <div className="rounded-2xl bg-sand px-4 py-3"><span className="block text-moss">Peligro</span><strong>{analysis.dangerCount}</strong></div>
            <div className="rounded-2xl bg-sand px-4 py-3"><span className="block text-moss">Revision</span><strong>{analysis.manualReviewCount}</strong></div>
          </div>
        </div>
      </article>

      <div className="space-y-6">
        {analysis.plants.map((plant) => (
          <article key={plant.plantGroupCode} className="rounded-[2rem] bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <h3 className="font-display text-2xl text-ink">{plant.plantGroupCode}</h3>
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${stateTone(plant.finalState)}`}>
                    {plant.finalState}
                  </span>
                </div>
                <p className="mt-2 text-sm text-moss">{plant.summary}</p>
                <p className="mt-2 text-xs uppercase tracking-[0.18em] text-moss">
                  QR representativo {plant.representativePlantQr} · {plant.evidenceCount} evidencias
                </p>
              </div>
              <div className="flex flex-wrap gap-2 text-xs">
                {plant.sides.map((side) => (
                  <span key={`${plant.plantGroupCode}-${side.side}`} className="rounded-full bg-sand px-3 py-1 text-ink">
                    Lado {side.side}: {side.dominantState} ({side.evidenceCount})
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {plant.evidenceImages.map((image) => (
                <figure key={image.imageId} className="overflow-hidden rounded-[1.5rem] border border-ink/10 bg-sand/40">
                  <img
                    src={absoluteImageUrl(image.imageUrl)}
                    alt={`${image.plantQr} lado ${image.plantSide}`}
                    className="h-56 w-full object-cover"
                  />
                  <figcaption className="space-y-2 p-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`rounded-full px-3 py-1 text-[11px] font-semibold ${stateTone(image.finalState)}`}>
                        {image.finalState}
                      </span>
                      {image.relevant ? (
                        <span className="rounded-full bg-ink px-3 py-1 text-[11px] font-semibold text-white">Relevante</span>
                      ) : null}
                    </div>
                    <p className="text-sm font-medium text-ink">{image.plantQr}</p>
                    <p className="text-xs text-moss">
                      Lado {image.plantSide} · Hint {image.statusHint} · Frame {image.sortOrder + 1}
                    </p>
                  </figcaption>
                </figure>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
