import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getRobotPatrolAnalysis, getRobotPatrolObservations } from "../../api/robotApi";
import { resolveBackendAssetUrl } from "../../utils/backendUrls";

type PatrolPlantAnalysis = {
  groupKey: string;
  plantNumber: string | null;
  potNumber: string | null;
  representativeExactQrLabel: string;
  plantGroupCode: string;
  representativePlantQr: string;
  operationalDate: string | null;
  finalState: string;
  summary: string;
  evidenceCount: number;
};

type PatrolAnalysis = {
  patrolId: string;
  totalGroups: number;
  healthyCount: number;
  attentionCount: number;
  dangerCount: number;
  manualReviewCount: number;
  inconclusiveCount: number;
  plants: PatrolPlantAnalysis[];
};

type ObservationImage = {
  id: number;
  sortOrder: number;
  relevant: boolean;
  imageUrl: string;
};

type Observation = {
  id: number;
  exactQrLabel: string;
  groupKey: string;
  plantNumber: string | null;
  potNumber: string | null;
  plantQr: string;
  plantSide: string;
  statusHint: string;
  operationalDate: string | null;
  scanSequence: number | null;
  analysisStatus: string;
  finalState: string | null;
  analysisNotes: string | null;
  images: ObservationImage[];
};

function resolveImageUrl(imageUrl: string) {
  return resolveBackendAssetUrl(imageUrl);
}

export function PatrolDetailPage() {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState<PatrolAnalysis | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setError("No se encontro el patrullaje solicitado.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    Promise.all([getRobotPatrolAnalysis(id), getRobotPatrolObservations(id)])
      .then(([analysisResponse, observationsResponse]) => {
        setAnalysis(analysisResponse as PatrolAnalysis);
        setObservations((observationsResponse as Observation[]) ?? []);
      })
      .catch((requestError) => {
        console.error("No se pudo cargar el detalle del patrullaje", requestError);
        setError("No se pudo cargar el detalle del patrullaje.");
      })
      .finally(() => setLoading(false));
  }, [id]);

  const relevantObservations = observations
    .map((observation) => ({
      ...observation,
      relevantImages: observation.images.filter((image) => image.relevant),
    }))
    .filter((observation) => observation.relevantImages.length > 0);

  const formatPlantLabel = (plantNumber: string | null, potNumber: string | null, fallback: string) => {
    if (!plantNumber || !potNumber) {
      return fallback;
    }
    return `Planta ${plantNumber} · Maceta ${potNumber}`;
  };

  if (loading) {
    return <section className="rounded-[2rem] bg-white p-6 shadow-sm">Cargando detalle del patrullaje...</section>;
  }

  if (error) {
    return <section className="rounded-[2rem] bg-white p-6 shadow-sm text-alert">{error}</section>;
  }

  return (
    <section className="space-y-6">
      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <p className="text-xs uppercase tracking-[0.18em] text-moss">Patrullaje {analysis?.patrolId ?? id}</p>
        <h2 className="mt-2 font-display text-3xl text-ink">Resumen de analisis</h2>
        <div className="mt-5 grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {[
            ["Grupos", analysis?.totalGroups ?? 0],
            ["Sanos", analysis?.healthyCount ?? 0],
            ["Atencion", analysis?.attentionCount ?? 0],
            ["Peligro", analysis?.dangerCount ?? 0],
            ["Revision", analysis?.manualReviewCount ?? 0],
            ["Inconcluso", analysis?.inconclusiveCount ?? 0],
          ].map(([label, value]) => (
            <article key={String(label)} className="rounded-[1.5rem] bg-sand p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-moss">{label}</p>
              <p className="mt-2 font-display text-4xl text-ink">{value}</p>
            </article>
          ))}
        </div>
      </article>

      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <h3 className="font-display text-2xl text-ink">Plantas consolidadas</h3>
        <div className="mt-5 grid gap-4">
          {(analysis?.plants ?? []).map((plant) => (
            <article key={plant.groupKey ?? plant.plantGroupCode} className="rounded-[1.5rem] border border-sand p-4">
              <div className="flex flex-wrap items-center gap-3">
                <span className="rounded-full bg-sand px-3 py-1 text-sm text-ink">
                  {formatPlantLabel(plant.plantNumber, plant.potNumber, plant.groupKey ?? plant.plantGroupCode)}
                </span>
                <span className="rounded-full bg-sand px-3 py-1 text-sm text-ink">{plant.finalState}</span>
                <span className="rounded-full bg-sand px-3 py-1 text-sm text-ink">{plant.evidenceCount} evidencias</span>
                {plant.operationalDate ? (
                  <span className="rounded-full bg-sand px-3 py-1 text-sm text-ink">Fecha {plant.operationalDate}</span>
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
          Este bloque expone las imagenes marcadas como relevantes por el backend para cada observacion del patrullaje.
        </p>
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          {relevantObservations.length > 0 ? (
            relevantObservations.map((observation) => (
              <article key={observation.id} className="rounded-[1.5rem] border border-sand p-4">
                <div className="flex flex-wrap items-center gap-3 text-sm text-moss">
                  <span className="rounded-full bg-sand px-3 py-1">
                    {formatPlantLabel(observation.plantNumber, observation.potNumber, observation.groupKey ?? observation.plantQr)}
                  </span>
                  <span className="rounded-full bg-sand px-3 py-1">Etiqueta {observation.exactQrLabel}</span>
                  <span className="rounded-full bg-sand px-3 py-1">{observation.finalState ?? observation.statusHint}</span>
                  <span className="rounded-full bg-sand px-3 py-1">{observation.analysisStatus}</span>
                  {observation.scanSequence !== null ? (
                    <span className="rounded-full bg-sand px-3 py-1">Escaneo #{observation.scanSequence}</span>
                  ) : null}
                  {observation.operationalDate ? (
                    <span className="rounded-full bg-sand px-3 py-1">Fecha {observation.operationalDate}</span>
                  ) : null}
                </div>
                {observation.analysisNotes ? <p className="mt-3 text-sm text-moss">{observation.analysisNotes}</p> : null}
                <p className="mt-2 text-sm text-moss">Lado observado: {observation.plantSide || "NA"}</p>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {observation.relevantImages.map((image) => (
                    <figure key={image.id} className="overflow-hidden rounded-[1.25rem] bg-sand">
                      <img
                        src={resolveImageUrl(image.imageUrl)}
                        alt={`Observacion ${observation.exactQrLabel} imagen ${image.sortOrder + 1}`}
                        className="h-48 w-full object-cover"
                      />
                      <figcaption className="px-3 py-2 text-xs uppercase tracking-[0.18em] text-moss">
                        Relevante · orden {image.sortOrder + 1}
                      </figcaption>
                    </figure>
                  ))}
                </div>
              </article>
            ))
          ) : (
            <p className="text-sm text-moss">No hay imagenes relevantes disponibles para este patrullaje.</p>
          )}
        </div>
      </article>
    </section>
  );
}
