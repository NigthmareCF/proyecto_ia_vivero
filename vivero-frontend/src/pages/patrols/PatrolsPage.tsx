import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getPatrols } from "../../api/patrolsApi";
import { finalizeRobotPatrolAnalysis, getRobotStatus, startRobotPatrol } from "../../api/robotApi";

type PatrolRecord = {
  id?: string | number;
  patrolId?: string;
  status?: string;
  startedAt?: string;
  observationsCount?: number;
};

type RobotStatus = {
  currentPatrolId?: string | null;
  connected?: boolean;
  mode?: string;
  currentPlantQr?: string | null;
};

function patrolKey(patrol: PatrolRecord) {
  return String(patrol.id ?? patrol.patrolId ?? "patrol");
}

export function PatrolsPage() {
  const navigate = useNavigate();
  const [patrols, setPatrols] = useState<PatrolRecord[]>([]);
  const [robotStatus, setRobotStatus] = useState<RobotStatus | null>(null);
  const [targetPatrolId, setTargetPatrolId] = useState("");
  const [startingPatrol, setStartingPatrol] = useState(false);
  const [finalizingPatrol, setFinalizingPatrol] = useState(false);

  useEffect(() => {
    getPatrols().then(setPatrols).catch(() => setPatrols([]));
    getRobotStatus().then(setRobotStatus).catch(() => setRobotStatus(null));
  }, []);

  const currentPatrolId = robotStatus?.currentPatrolId?.trim();

  async function handleStartPatrol() {
    if (startingPatrol) return;
    setStartingPatrol(true);
    try {
      await startRobotPatrol();
      const refreshedStatus = await getRobotStatus();
      setRobotStatus(refreshedStatus);
    } catch (error) {
      console.error("No se pudo iniciar el patrullaje", error);
    } finally {
      setStartingPatrol(false);
    }
  }

  async function handleFinalizePatrol() {
    if (!currentPatrolId || finalizingPatrol) return;
    setFinalizingPatrol(true);
    try {
      await finalizeRobotPatrolAnalysis(currentPatrolId);
      const refreshedStatus = await getRobotStatus();
      setRobotStatus(refreshedStatus);
      navigate(`/patrols/${encodeURIComponent(currentPatrolId)}`);
    } catch (error) {
      console.error("No se pudo finalizar el patrullaje activo", error);
    } finally {
      setFinalizingPatrol(false);
    }
  }

  return (
    <section className="space-y-6">
      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <p className="text-xs uppercase tracking-[0.18em] text-moss">Operacion robot</p>
        <h2 className="mt-2 font-display text-3xl text-ink">Patrullajes</h2>
        <p className="mt-2 max-w-2xl text-sm text-moss">
          Las evidencias se guardan durante el recorrido. El reporte completo se consulta cuando el robot finaliza y el backend marca el analisis como finalizado.
        </p>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <article className="rounded-[1.5rem] bg-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Robot</p>
            <p className="mt-2 text-sm font-semibold text-ink">{robotStatus?.connected ? "Conectado" : "Sin conexion"}</p>
          </article>
          <article className="rounded-[1.5rem] bg-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Modo</p>
            <p className="mt-2 text-sm font-semibold text-ink">{robotStatus?.mode ?? "Sin datos"}</p>
          </article>
          <article className="rounded-[1.5rem] bg-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Patrullaje actual</p>
            <p className="mt-2 text-sm font-semibold text-ink">{currentPatrolId ?? "Sin patrullaje"}</p>
          </article>
        </div>
        <div className="mt-5 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleStartPatrol}
            disabled={startingPatrol || !robotStatus?.connected}
            className="rounded-2xl bg-ink px-5 py-3 text-sm font-semibold text-white transition hover:bg-clay disabled:bg-moss/40"
          >
            {startingPatrol ? "Iniciando..." : "Iniciar patrullaje"}
          </button>
          <button
            type="button"
            onClick={handleFinalizePatrol}
            disabled={finalizingPatrol || !currentPatrolId}
            className="rounded-2xl border border-clay px-5 py-3 text-sm font-semibold text-ink transition hover:border-ink disabled:border-moss/40 disabled:text-moss/40"
          >
            {finalizingPatrol ? "Finalizando..." : "Finalizar patrullaje"}
          </button>
          {currentPatrolId ? (
            <Link
              to={`/patrols/${encodeURIComponent(currentPatrolId)}`}
              className="rounded-2xl border border-sand px-5 py-3 text-sm font-semibold text-ink transition hover:border-clay"
            >
              Abrir patrullaje actual
            </Link>
          ) : null}
        </div>
      </article>

      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <h3 className="font-display text-2xl text-ink">Abrir analisis de patrullaje</h3>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <input
            className="flex-1 rounded-2xl border border-ink/10 px-4 py-3 text-sm outline-none transition focus:border-clay"
            placeholder="PATROL-2026-05-07"
            value={targetPatrolId}
            onChange={(event) => setTargetPatrolId(event.target.value)}
          />
          <Link
            to={targetPatrolId.trim() ? `/patrols/${encodeURIComponent(targetPatrolId.trim())}` : "#"}
            className={`rounded-2xl px-5 py-3 text-center text-sm font-semibold text-white transition ${
              targetPatrolId.trim() ? "bg-ink hover:bg-clay" : "pointer-events-none bg-moss/40"
            }`}
          >
            Abrir reporte
          </Link>
          {currentPatrolId ? (
            <Link
              to={`/patrols/${encodeURIComponent(currentPatrolId)}`}
              className="rounded-2xl border border-sand px-5 py-3 text-center text-sm font-semibold text-ink transition hover:border-clay"
            >
              Ver actual
            </Link>
          ) : null}
        </div>
      </article>

      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <h3 className="font-display text-2xl text-ink">Historial disponible</h3>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {patrols.length > 0 ? (
            patrols.map((patrol) => (
              <Link
                key={patrolKey(patrol)}
                to={`/patrols/${encodeURIComponent(patrolKey(patrol))}`}
                className="rounded-[1.5rem] border border-sand p-4 transition hover:border-clay"
              >
                <p className="font-semibold text-ink">Patrullaje {patrolKey(patrol)}</p>
                <p className="mt-2 text-sm text-moss">{patrol.status ?? "Estado no informado"}</p>
                <p className="mt-2 text-xs uppercase tracking-[0.18em] text-moss">
                  {patrol.observationsCount ?? 0} observaciones
                </p>
              </Link>
            ))
          ) : (
            <p className="text-sm text-moss">
              El backend actual no expone una lista historica de patrullajes. Usa el ID del patrullaje actual o escribe un ID especifico para abrir su analisis.
            </p>
          )}
        </div>
      </article>
    </section>
  );
}
