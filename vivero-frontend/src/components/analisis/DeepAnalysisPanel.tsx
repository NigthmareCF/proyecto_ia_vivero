import { useEffect, useMemo, useState } from "react";
import { getAnalysisHistory, type AnalysisHistoryItem } from "../../api/analisisApi";
import { getRobotPatrolAnalysis } from "../../api/robotApi";
import type { PatrolAnalysis, PatrolPlantAnalysis } from "../../types/patrolAnalysis";
import { resolveBackendAssetUrl } from "../../utils/backendUrls";

export function DeepAnalysisPanel() {
  const [patrolId, setPatrolId] = useState("");
  const [patrol, setPatrol] = useState<PatrolAnalysis | null>(null);
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
  const [selectedPlant, setSelectedPlant] = useState<PatrolPlantAnalysis | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    getAnalysisHistory().then(setHistory).catch(() => setMessage("No se pudo cargar el historial de analisis."));
  }, []);

  async function loadPatrol() {
    if (!patrolId.trim()) return;
    setMessage(null);
    setSelectedPlant(null);
    try {
      setPatrol((await getRobotPatrolAnalysis(patrolId.trim())) as PatrolAnalysis);
    } catch {
      setPatrol(null);
      setMessage("No se pudo cargar el patrullaje indicado.");
    }
  }

  const matchingHistory = useMemo(() => {
    if (!selectedPlant) return [];
    return history.filter(
      (record) =>
        record.generalLabels.includes(selectedPlant.plantGroupCode)
        || record.exactLabels.includes(selectedPlant.representativePlantQr),
    );
  }, [history, selectedPlant]);

  return (
    <section className="space-y-6">
      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <h2 className="font-display text-3xl text-ink">Analisis profundo</h2>
        <p className="mt-2 text-sm text-moss">Filtre por patrullaje para revisar plantas, anotaciones, evidencias y reportes especificos.</p>
        <div className="mt-5 flex gap-3">
          <input className="min-w-0 flex-1 rounded-2xl border border-ink/10 px-4 py-3" value={patrolId} onChange={(event) => setPatrolId(event.target.value)} placeholder="Numero o codigo de patrullaje" />
          <button type="button" onClick={loadPatrol} className="rounded-2xl bg-ink px-5 py-3 text-sm font-semibold text-white">Buscar</button>
        </div>
        {message ? <p className="mt-3 text-sm text-alert">{message}</p> : null}
      </article>

      <div className="grid gap-6 xl:grid-cols-[0.75fr_1.25fr]">
        <details className="rounded-[2rem] bg-white p-6 shadow-sm" open>
          <summary className="cursor-pointer font-display text-2xl text-ink">Plantas escaneadas</summary>
          <div className="mt-4 grid gap-3">
            {(patrol?.plants ?? []).map((plant) => (
              <button
                type="button"
                key={plant.plantGroupCode}
                onClick={() => setSelectedPlant(plant)}
                className={`rounded-2xl border px-4 py-3 text-left ${selectedPlant?.plantGroupCode === plant.plantGroupCode ? "border-clay bg-clay/10" : "border-sand"}`}
              >
                <strong className="text-sm text-ink">{plant.plantGroupCode}</strong>
                <span className="mt-1 block text-xs text-moss">{plant.finalState} · {plant.evidenceCount} evidencias</span>
              </button>
            ))}
            {patrol && patrol.plants.length === 0 ? <p className="text-sm text-moss">No hay plantas consolidadas.</p> : null}
          </div>
        </details>

        <article className="rounded-[2rem] bg-white p-6 shadow-sm">
          {!selectedPlant ? <p className="text-sm text-moss">Seleccione una planta para ver su detalle.</p> : (
            <>
              <h3 className="font-display text-2xl text-ink">{selectedPlant.plantGroupCode}</h3>
              <p className="mt-2 text-sm text-moss">{selectedPlant.summary}</p>
              <div className="mt-4 grid gap-3">
                {selectedPlant.observations.map((observation) => (
                  <details key={observation.observationId} className="rounded-2xl border border-sand p-4">
                    <summary className="cursor-pointer text-sm font-semibold text-ink">
                      {observation.plantQr} · {observation.analysisStatus} · {observation.finalState ?? observation.statusHint}
                    </summary>
                    <p className="mt-2 text-sm text-moss">{observation.analysisNotes || "Sin anotaciones para esta observacion."}</p>
                  </details>
                ))}
              </div>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                {selectedPlant.evidenceImages.map((image) => (
                  <img key={image.imageId} src={resolveBackendAssetUrl(image.imageUrl)} alt={`Evidencia ${image.imageId}`} className="h-44 w-full rounded-2xl object-cover" />
                ))}
              </div>
              <h4 className="mt-6 font-display text-xl text-ink">Reportes especificos</h4>
              <div className="mt-3 grid gap-3">
                {matchingHistory.map((record) => (
                  <article key={record.id} className="rounded-2xl bg-sand p-4">
                    <p className="text-xs uppercase tracking-[0.14em] text-moss">Registro #{record.id}{record.reportId ? ` · Reporte #${record.reportId}` : ""}</p>
                    <p className="mt-2 text-sm font-semibold text-ink">{record.reportTitle || record.estadoGeneral}</p>
                    <p className="mt-2 text-sm text-moss">{record.summaryText}</p>
                    {record.operatorNotes ? <p className="mt-2 text-sm text-moss">Anotaciones: {record.operatorNotes}</p> : null}
                    {record.hallazgos.length ? <p className="mt-2 text-sm text-moss">Hallazgos: {record.hallazgos.join(" · ")}</p> : null}
                    {record.recomendaciones.length ? <p className="mt-2 text-sm text-moss">Recomendaciones: {record.recomendaciones.join(" · ")}</p> : null}
                  </article>
                ))}
                {matchingHistory.length === 0 ? <p className="text-sm text-moss">No hay reportes especificos asociados a esta planta.</p> : null}
              </div>
            </>
          )}
        </article>
      </div>
    </section>
  );
}
