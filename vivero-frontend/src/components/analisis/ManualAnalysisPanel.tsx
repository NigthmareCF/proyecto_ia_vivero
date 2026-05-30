import { useState } from "react";
import { createManualAnalysis, type AnalysisHistoryItem } from "../../api/analisisApi";
import { getRobotPatrolAnalysis } from "../../api/robotApi";
import type { PatrolAnalysis, PatrolPlantAnalysis } from "../../types/patrolAnalysis";
import { fileToAnalysisImage, splitListInput } from "./analysisUtils";

const states = ["SANO", "ATENCION", "PELIGRO", "REVISION_MANUAL"];
const urgencyLevels = ["BAJA", "MEDIA", "ALTA", "CRITICA"];

export function ManualAnalysisPanel() {
  const [patrolId, setPatrolId] = useState("");
  const [patrol, setPatrol] = useState<PatrolAnalysis | null>(null);
  const [selectedPlant, setSelectedPlant] = useState<PatrolPlantAnalysis | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [estadoGeneral, setEstadoGeneral] = useState("REVISION_MANUAL");
  const [urgencia, setUrgencia] = useState("MEDIA");
  const [confianza, setConfianza] = useState("0.85");
  const [reporteManual, setReporteManual] = useState("");
  const [operatorNotes, setOperatorNotes] = useState("");
  const [hallazgos, setHallazgos] = useState("");
  const [recomendaciones, setRecomendaciones] = useState("");
  const [reportTitle, setReportTitle] = useState("");
  const [createReport, setCreateReport] = useState(true);
  const [loadingPatrol, setLoadingPatrol] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedRecord, setSavedRecord] = useState<AnalysisHistoryItem | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function loadPatrol() {
    if (!patrolId.trim()) return;
    setLoadingPatrol(true);
    setMessage(null);
    setSelectedPlant(null);
    try {
      setPatrol((await getRobotPatrolAnalysis(patrolId.trim())) as PatrolAnalysis);
    } catch {
      setPatrol(null);
      setMessage("No se pudo cargar el patrullaje indicado.");
    } finally {
      setLoadingPatrol(false);
    }
  }

  async function saveManualAnalysis() {
    if (!file || !selectedPlant || !reporteManual.trim()) {
      setMessage("Seleccione patrullaje, planta, imagen y escriba el reporte manual.");
      return;
    }

    setSaving(true);
    setMessage(null);
    try {
      const image = await fileToAnalysisImage(file);
      const parsedPatrolId = Number(patrolId);
      const numericPatrolId = Number.isSafeInteger(parsedPatrolId) && parsedPatrolId > 0 ? parsedPatrolId : undefined;
      const record = await createManualAnalysis({
        images: [image],
        generalLabels: [selectedPlant.plantGroupCode],
        exactLabels: [selectedPlant.representativePlantQr],
        estadoGeneral,
        urgencia,
        confianza: Number(confianza),
        reporteManual: reporteManual.trim(),
        operatorNotes: operatorNotes.trim(),
        hallazgos: splitListInput(hallazgos),
        recomendaciones: splitListInput(recomendaciones),
        patrolId: numericPatrolId,
        createStandaloneReport: createReport,
        reportTitle: reportTitle.trim(),
      });
      setSavedRecord(record);
      setMessage(
        numericPatrolId
          ? "Registro manual guardado y asociado al patrullaje."
          : "Registro guardado por etiquetas. El identificador del patrullaje no es numerico y no se persistio como ID.",
      );
    } catch {
      setMessage("No se pudo guardar el registro manual.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <h2 className="font-display text-3xl text-ink">Registro manual</h2>
        <p className="mt-2 text-sm text-moss">Seleccione el patrullaje y la planta escaneada antes de registrar el criterio humano.</p>
        <div className="mt-5 flex gap-3">
          <input
            className="min-w-0 flex-1 rounded-2xl border border-ink/10 px-4 py-3"
            value={patrolId}
            onChange={(event) => setPatrolId(event.target.value)}
            placeholder="Numero o codigo de patrullaje"
          />
          <button type="button" onClick={loadPatrol} className="rounded-2xl bg-ink px-5 py-3 text-sm font-semibold text-white">
            {loadingPatrol ? "Cargando..." : "Buscar"}
          </button>
        </div>
        <details className="mt-5 rounded-2xl border border-sand p-4" open>
          <summary className="cursor-pointer font-semibold text-ink">Plantas escaneadas</summary>
          <div className="mt-3 grid gap-2">
            {(patrol?.plants ?? []).map((plant) => (
              <button
                key={plant.plantGroupCode}
                type="button"
                onClick={() => setSelectedPlant(plant)}
                className={`rounded-2xl border px-4 py-3 text-left text-sm ${
                  selectedPlant?.plantGroupCode === plant.plantGroupCode ? "border-clay bg-clay/10" : "border-sand"
                }`}
              >
                <strong>{plant.plantGroupCode}</strong>
                <span className="ml-2 text-moss">{plant.representativePlantQr}</span>
                <span className="mt-1 block text-xs text-moss">{plant.finalState} · {plant.evidenceCount} evidencias</span>
              </button>
            ))}
            {patrol && patrol.plants.length === 0 ? <p className="text-sm text-moss">El patrullaje no tiene plantas consolidadas.</p> : null}
          </div>
        </details>
        {selectedPlant ? <p className="mt-4 text-sm text-moss">Seleccionada: <strong>{selectedPlant.plantGroupCode}</strong></p> : null}
      </article>

      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <h3 className="font-display text-2xl text-ink">Criterio del operador</h3>
        <input className="mt-4 w-full rounded-2xl border border-ink/10 px-4 py-3" type="file" accept="image/*" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <select className="rounded-2xl border border-ink/10 px-4 py-3" value={estadoGeneral} onChange={(event) => setEstadoGeneral(event.target.value)}>
            {states.map((state) => <option key={state}>{state}</option>)}
          </select>
          <select className="rounded-2xl border border-ink/10 px-4 py-3" value={urgencia} onChange={(event) => setUrgencia(event.target.value)}>
            {urgencyLevels.map((level) => <option key={level}>{level}</option>)}
          </select>
          <input className="rounded-2xl border border-ink/10 px-4 py-3" type="number" min="0" max="1" step="0.05" value={confianza} onChange={(event) => setConfianza(event.target.value)} placeholder="Confianza 0-1" />
        </div>
        <textarea className="mt-4 min-h-32 w-full rounded-2xl border border-ink/10 px-4 py-3" value={reporteManual} onChange={(event) => setReporteManual(event.target.value)} placeholder="Reporte especifico de la planta" />
        <textarea className="mt-4 min-h-24 w-full rounded-2xl border border-ink/10 px-4 py-3" value={operatorNotes} onChange={(event) => setOperatorNotes(event.target.value)} placeholder="Anotaciones del operador" />
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          <textarea className="min-h-24 rounded-2xl border border-ink/10 px-4 py-3" value={hallazgos} onChange={(event) => setHallazgos(event.target.value)} placeholder={"Hallazgos, uno por linea"} />
          <textarea className="min-h-24 rounded-2xl border border-ink/10 px-4 py-3" value={recomendaciones} onChange={(event) => setRecomendaciones(event.target.value)} placeholder={"Recomendaciones, una por linea"} />
        </div>
        <input className="mt-4 w-full rounded-2xl border border-ink/10 px-4 py-3" value={reportTitle} onChange={(event) => setReportTitle(event.target.value)} placeholder="Titulo del reporte PDF" />
        <label className="mt-4 flex items-center gap-2 text-sm text-moss">
          <input type="checkbox" checked={createReport} onChange={(event) => setCreateReport(event.target.checked)} />
          Generar reporte PDF individual
        </label>
        <button type="button" onClick={saveManualAnalysis} disabled={saving} className="mt-4 rounded-2xl bg-clay px-5 py-3 font-semibold text-white disabled:bg-moss/40">
          {saving ? "Guardando..." : "Guardar registro manual"}
        </button>
        {message ? <p className="mt-3 text-sm text-moss">{message}</p> : null}
        {savedRecord?.reportId ? <p className="mt-2 text-sm text-moss">Reporte generado: #{savedRecord.reportId} · {savedRecord.reportTitle}</p> : null}
      </article>
    </section>
  );
}
