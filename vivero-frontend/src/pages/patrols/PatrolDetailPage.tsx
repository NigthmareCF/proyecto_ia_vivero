import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { createReport, finalizeRobotPatrolAnalysis, getRobotPatrolAnalysis } from "../../api/robotApi";
import { resolveBackendAssetUrl } from "../../utils/backendUrls";

type PatrolEvidenceImage = {
  observationId: number;
  imageId: number;
  imageUrl: string;
  mimeType: string;
  sortOrder: number;
  relevant: boolean;
  plantQr: string;
  plantSide: string;
  statusHint: string;
  finalState: string | null;
  observedAt: string | null;
};

type PatrolObservation = {
  observationId: number;
  plantQr: string;
  plantSide: string;
  statusHint: string;
  finalState: string | null;
  analysisStatus: string;
  analysisNotes: string | null;
  observedAt: string | null;
};

type PatrolPlantAnalysis = {
  patrolId: string;
  plantGroupCode: string;
  representativePlantQr: string;
  finalState: string;
  summary: string;
  evidenceCount: number;
  lastObservedAt: string | null;
  evidenceImages: PatrolEvidenceImage[];
  observations: PatrolObservation[];
};

type PatrolAnalysis = {
  robotId: string;
  patrolId: string;
  totalGroups: number;
  healthyCount: number;
  attentionCount: number;
  dangerCount: number;
  manualReviewCount: number;
  inconclusiveCount: number;
  plants: PatrolPlantAnalysis[];
};

function resolveImageUrl(imageUrl: string) {
  return resolveBackendAssetUrl(imageUrl);
}

function formatPlantLabel(groupCode: string, fallback: string) {
  const match = groupCode.match(/PLA[_-]?(\d+).*MA[_-]?(\d+)/i);
  if (!match) {
    return fallback;
  }
  return `Planta ${match[1]} - Maceta ${match[2]}`;
}

function stateClassName(state?: string | null) {
  if (state === "PELIGRO") return "bg-alert text-white";
  if (state === "ATENCION" || state === "REVISION_MANUAL") return "bg-clay text-white";
  if (state === "SANO") return "bg-moss text-white";
  return "bg-sand text-ink";
}

export function PatrolDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<PatrolAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [finalizing, setFinalizing] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPatrolAnalysis = () => {
    if (!id) {
      setError("No se encontro el patrullaje solicitado.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    getRobotPatrolAnalysis(id)
      .then((analysisResponse) => setAnalysis(analysisResponse as PatrolAnalysis))
      .catch((requestError) => {
        console.error("No se pudo cargar el detalle del patrullaje", requestError);
        setError("No se pudo cargar el detalle del patrullaje.");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadPatrolAnalysis();
  }, [id]);

  const allObservations = useMemo(
    () => (analysis?.plants ?? []).flatMap((plant) => plant.observations ?? []),
    [analysis],
  );
  const isFinalized = allObservations.length > 0 && allObservations.every((observation) => observation.analysisStatus === "FINALIZED");
  const relevantImages = useMemo(
    () =>
      (analysis?.plants ?? []).flatMap((plant) =>
        (plant.evidenceImages ?? [])
          .filter((image) => image.relevant)
          .slice(0, 4)
          .map((image) => ({ ...image, plantGroupCode: plant.plantGroupCode, plantSummary: plant.summary })),
      ),
    [analysis],
  );
  const storedImagesCount = (analysis?.plants ?? []).reduce((total, plant) => total + (plant.evidenceImages?.length ?? 0), 0);

  async function handleFinalize() {
    if (!id || finalizing) return;
    setFinalizing(true);
    setError(null);
    try {
      const response = await finalizeRobotPatrolAnalysis(id);
      setAnalysis(response as PatrolAnalysis);
    } catch (requestError) {
      console.error("No se pudo finalizar el analisis de patrullaje", requestError);
      setError("No se pudo finalizar el analisis del patrullaje.");
    } finally {
      setFinalizing(false);
    }
  }

  async function handleGenerateReport() {
    if (!analysis || generatingReport || !id) return;
    setGeneratingReport(true);
    setError(null);
    try {
      const patrolNumericId = Number(id);
      if (!Number.isFinite(patrolNumericId)) {
        throw new Error("Patrol ID must be numeric to generate a report");
      }
      const report = await createReport({
        patrolId: patrolNumericId,
        title: `Reporte de patrullaje ${analysis.patrolId}`,
        summary: `Consolidado del patrullaje ${analysis.patrolId}.`,
        observationsCount: analysis.totalGroups,
        healthyCount: analysis.healthyCount,
        attentionCount: analysis.attentionCount,
        dangerCount: analysis.dangerCount,
        manualReviewCount: analysis.manualReviewCount,
        inconclusiveCount: analysis.inconclusiveCount,
        plantDetails: (analysis.plants ?? []).map((plant) => ({
          plantGroupCode: plant.plantGroupCode,
          finalState: plant.finalState,
          summary: plant.summary,
          findings: (plant.observations ?? []).map((observation) => ({
            side: observation.plantSide || "NA",
            note: observation.analysisNotes || observation.statusHint || observation.finalState || "Sin detalle",
          })),
        })),
        analysisProvider: "robot",
        analysisModel: "patrullaje-consolidado",
        analysisNotes: "Reporte generado desde el cierre de patrullaje consolidado.",
      });
      navigate(`/reports`, { replace: false });
      console.info("Reporte generado", report);
    } catch (requestError) {
      console.error("No se pudo generar el reporte del patrullaje", requestError);
      setError("No se pudo generar el reporte del patrullaje.");
    } finally {
      setGeneratingReport(false);
    }
  }

  if (loading) {
    return <section className="rounded-[2rem] bg-white p-6 shadow-sm">Cargando detalle del patrullaje...</section>;
  }

  if (error && !analysis) {
    return <section className="rounded-[2rem] bg-white p-6 shadow-sm text-alert">{error}</section>;
  }

  return (
    <section className="space-y-6">
      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Patrullaje {analysis?.patrolId ?? id}</p>
            <h2 className="mt-2 font-display text-3xl text-ink">
              {isFinalized ? "Reporte consolidado" : "Captura en progreso"}
            </h2>
            <p className="mt-3 max-w-3xl text-sm text-moss">
              {isFinalized
                ? "El robot ya cerro el recorrido. Se habilitan el resumen, las plantas consolidadas y las imagenes relevantes."
                : "El backend puede seguir guardando datos mientras el robot patrulla. El reporte completo se desbloquea cuando llega la senal de cierre."}
            </p>
          </div>
          <button
            type="button"
            onClick={handleFinalize}
            disabled={finalizing || !analysis}
            className="rounded-2xl bg-ink px-5 py-3 text-sm font-semibold text-white transition hover:bg-clay disabled:bg-moss/40"
          >
            {finalizing ? "Finalizando..." : "Finalizar analisis"}
          </button>
        </div>
        {isFinalized ? (
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleGenerateReport}
              disabled={generatingReport}
              className="rounded-2xl bg-ink px-5 py-3 text-sm font-semibold text-white transition hover:bg-clay disabled:bg-moss/40"
            >
              {generatingReport ? "Generando reporte..." : "Generar reporte"}
            </button>
            <Link
              to="/reports"
              className="rounded-2xl bg-clay px-5 py-3 text-sm font-semibold text-white transition hover:bg-ink"
            >
              Ir a reportes
            </Link>
            <Link
              to="/patrols"
              className="rounded-2xl border border-sand px-5 py-3 text-sm font-semibold text-ink transition hover:border-clay"
            >
              Volver a patrullajes
            </Link>
          </div>
        ) : null}
        {error ? <p className="mt-3 text-sm text-alert">{error}</p> : null}
        <div className="mt-5 grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {[
            ["Grupos", analysis?.totalGroups ?? 0],
            ["Imagenes", storedImagesCount],
            ["Sanos", analysis?.healthyCount ?? 0],
            ["Atencion", analysis?.attentionCount ?? 0],
            ["Peligro", analysis?.dangerCount ?? 0],
            ["Estado", isFinalized ? "Final" : "Pendiente"],
          ].map(([label, value]) => (
            <article key={String(label)} className="rounded-[1.5rem] bg-sand p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-moss">{label}</p>
              <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
            </article>
          ))}
        </div>
      </article>

      {!isFinalized ? (
        <article className="rounded-[2rem] bg-white p-6 shadow-sm">
          <h3 className="font-display text-2xl text-ink">Reporte bloqueado hasta cierre</h3>
          <p className="mt-3 text-sm text-moss">
            Esta pantalla mantiene el retraso justificado: durante el recorrido se acumulan rafagas, clasificacion local y cola VLM. Al finalizar, se presentan plantas, imagenes relevantes y reporte general.
          </p>
        </article>
      ) : null}

      {isFinalized ? (
        <>
          <article className="rounded-[2rem] bg-white p-6 shadow-sm">
            <h3 className="font-display text-2xl text-ink">Plantas consolidadas</h3>
            <div className="mt-5 grid gap-4">
              {(analysis?.plants ?? []).map((plant) => (
                <article key={plant.plantGroupCode} className="rounded-[1.5rem] border border-sand p-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="rounded-full bg-sand px-3 py-1 text-sm text-ink">
                      {formatPlantLabel(plant.plantGroupCode, plant.plantGroupCode)}
                    </span>
                    <span className={`rounded-full px-3 py-1 text-sm ${stateClassName(plant.finalState)}`}>{plant.finalState}</span>
                    <span className="rounded-full bg-sand px-3 py-1 text-sm text-ink">{plant.evidenceCount} evidencias</span>
                    {plant.lastObservedAt ? (
                      <span className="rounded-full bg-sand px-3 py-1 text-sm text-ink">
                        Ultima lectura {new Date(plant.lastObservedAt).toLocaleString()}
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-3 text-sm text-moss">{plant.summary}</p>
                </article>
              ))}
            </div>
          </article>

          <article className="rounded-[2rem] bg-white p-6 shadow-sm">
            <h3 className="font-display text-2xl text-ink">Imagenes relevantes</h3>
            <p className="mt-2 text-sm text-moss">
              Se muestran solo las evidencias marcadas como relevantes por el backend para que el reporte final no se llene con toda la rafaga.
            </p>
            <div className="mt-5 grid gap-5 lg:grid-cols-2">
              {relevantImages.length > 0 ? (
                relevantImages.map((image) => (
                  <article key={`${image.observationId}-${image.imageId}`} className="rounded-[1.5rem] border border-sand p-4">
                    <div className="flex flex-wrap items-center gap-3 text-sm text-moss">
                      <span className="rounded-full bg-sand px-3 py-1">
                        {formatPlantLabel(image.plantGroupCode, image.plantGroupCode)}
                      </span>
                      <span className="rounded-full bg-sand px-3 py-1">QR {image.plantQr}</span>
                      <span className="rounded-full bg-sand px-3 py-1">{image.finalState ?? image.statusHint}</span>
                      <span className="rounded-full bg-sand px-3 py-1">Orden {image.sortOrder + 1}</span>
                    </div>
                    <p className="mt-3 text-sm text-moss">{image.plantSummary}</p>
                    <figure className="mt-4 overflow-hidden rounded-[1.25rem] bg-sand">
                      <img
                        src={resolveImageUrl(image.imageUrl)}
                        alt={`Evidencia ${image.imageId}`}
                        className="h-56 w-full object-cover"
                      />
                      <figcaption className="px-3 py-2 text-xs uppercase tracking-[0.18em] text-moss">
                        Imagen relevante - lado {image.plantSide || "NA"}
                      </figcaption>
                    </figure>
                  </article>
                ))
              ) : (
                <p className="text-sm text-moss">No hay imagenes relevantes disponibles para este patrullaje.</p>
              )}
            </div>
          </article>
        </>
      ) : null}
    </section>
  );
}
