import { useEffect } from "react";
import {
  sendRobotCommand,
  setRobotMode,
  setRobotSpeedProfile,
  switchRobotCamera,
} from "../../api/robotApi";
import { useRobotWebSocket } from "../../hooks/useRobotWebSocket";
import { useRobotStore } from "../../store/robotStore";

const commandLabels: Record<string, string> = {
  FORWARD: "Avanzar",
  LEFT: "Izquierda",
  RIGHT: "Derecha",
  STOP: "Detener",
};

const connectionTone: Record<string, string> = {
  EXCELLENT: "bg-emerald-500",
  GOOD: "bg-lime-500",
  FAIR: "bg-amber-400",
  WEAK: "bg-orange-500",
  OFFLINE: "bg-rose-500",
};

const cameraHotkeys: Record<string, "FRONT" | "LEFT" | "RIGHT"> = {
  "1": "FRONT",
  "2": "LEFT",
  "3": "RIGHT",
};

const speedHotkeys: Record<string, "LOW" | "MEDIUM" | "HIGH" | "TURBO"> = {
  q: "LOW",
  w: "MEDIUM",
  e: "HIGH",
  r: "TURBO",
};

function formatMetric(value: number | null, suffix: string) {
  return value === null ? "--" : `${Math.round(value)}${suffix}`;
}

export function RobotControlPage() {
  const robot = useRobotStore();
  useRobotWebSocket();

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      if (cameraHotkeys[event.key]) {
        void switchRobotCamera(cameraHotkeys[event.key]);
      } else if (key === "m") {
        void setRobotMode("MANUAL_FREE");
      } else if (key === "a") {
        void setRobotMode("AUTO_LINE");
      } else if (key === "x") {
        void setRobotMode("ACRO");
      } else if (speedHotkeys[key]) {
        void setRobotSpeedProfile(speedHotkeys[key]);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const connectionClass = connectionTone[robot.connectionQuality] ?? "bg-clay";
  const batteryWidth = Math.min(Math.max(robot.batteryLevel, 0), 100);
  const cpuWidth = Math.min(Math.max(robot.cpuUsage ?? 0, 0), 100);

  return (
    <section className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <h2 className="font-display text-3xl">Control del robot</h2>
        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-moss">
          <span className="rounded-full bg-sand px-3 py-1">Modo {robot.mode}</span>
          <span className="rounded-full bg-sand px-3 py-1">Perfil {robot.controlProfile}</span>
          <span className="rounded-full bg-sand px-3 py-1">Camara {robot.activeCamera}</span>
          <span className="rounded-full bg-sand px-3 py-1">Potencia {robot.speedProfile}</span>
          <span className="rounded-full bg-sand px-3 py-1">QR {robot.currentPlantQr ?? "sin objetivo"}</span>
          <span className="inline-flex items-center gap-2 rounded-full bg-sand px-3 py-1">
            <span className={`h-2.5 w-2.5 rounded-full ${connectionClass}`} />
            {robot.isConnected ? robot.connectionQuality : "OFFLINE"}
          </span>
        </div>

        <p className="mt-4 text-sm text-moss">{robot.statusSummary}</p>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <article className="rounded-[1.5rem] bg-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Bateria</p>
            <p className="mt-2 font-display text-4xl text-ink">{robot.batteryLevel}%</p>
            <div className="mt-3 h-3 rounded-full bg-white/80">
              <div className="h-3 rounded-full bg-ink" style={{ width: `${batteryWidth}%` }} />
            </div>
          </article>
          <article className="rounded-[1.5rem] bg-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Temperatura CPU</p>
            <p className="mt-2 font-display text-4xl text-ink">{formatMetric(robot.temperatureCelsius, "C")}</p>
            <p className="mt-3 text-sm text-moss">Uso del procesador {formatMetric(robot.cpuUsage, "%")}</p>
            <div className="mt-2 h-2 rounded-full bg-white/80">
              <div className="h-2 rounded-full bg-clay" style={{ width: `${cpuWidth}%` }} />
            </div>
          </article>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <article className="rounded-[1.5rem] border border-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Cola local</p>
            <p className="mt-2 font-display text-3xl text-ink">{robot.queueDepth}</p>
          </article>
          <article className="rounded-[1.5rem] border border-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Stream</p>
            <p className="mt-2 font-display text-3xl text-ink">{robot.streamActive ? "Activo" : "Inactivo"}</p>
          </article>
          <article className="rounded-[1.5rem] border border-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Obstaculo</p>
            <p className={`mt-2 font-display text-3xl ${robot.obstacleDetected ? "text-alert" : "text-ink"}`}>
              {robot.obstacleDetected ? "Detectado" : "Libre"}
            </p>
          </article>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3">
          {["FORWARD", "LEFT", "RIGHT", "STOP"].map((command) => (
            <button
              key={command}
              className="rounded-2xl bg-ink px-4 py-3 text-white transition hover:bg-clay"
              onClick={() => sendRobotCommand(command)}
            >
              {commandLabels[command] ?? command}
            </button>
          ))}
        </div>
      </article>

      <article className="rounded-[2rem] bg-ink p-6 text-sand shadow-sm">
        <h2 className="font-display text-3xl">Camara y estado</h2>
        <div className="mt-4 grid gap-4">
          <div className="relative grid min-h-80 place-items-center overflow-hidden rounded-[1.5rem] border border-white/20 bg-white/5">
            <div className="absolute inset-x-0 top-0 flex items-center justify-between bg-gradient-to-b from-black/45 to-transparent px-4 py-3 text-xs uppercase tracking-[0.18em] text-sand">
              <span>Recorrido en vivo</span>
              <span>{robot.activeCamera} · {robot.streamActive ? "stream activo" : "stream en espera"}</span>
            </div>
            <div className="text-center">
              <p className="font-display text-4xl">{robot.streamActive ? robot.activeCamera : "Sin video"}</p>
              <p className="mt-2 text-sm text-sand/70">
                Cambio de camara por teclado: `1` frontal, `2` izquierda, `3` derecha.
              </p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <article className="rounded-[1.5rem] border border-white/15 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-sand/70">Perfiles</p>
              <p className="mt-3 text-sm leading-6 text-sand/85">
                `A` auto-linea · `M` manual libre · `X` acrobacia
              </p>
              <p className="mt-2 text-sm leading-6 text-sand/85">
                `Q/W/E/R` bajo, medio, alto, turbo
              </p>
            </article>

            <article className="rounded-[1.5rem] border border-white/15 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-sand/70">Resumen operativo</p>
              <p className="mt-3 text-sm leading-6 text-sand/85">{robot.statusSummary}</p>
            </article>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {[
              ["Bateria", `${robot.batteryLevel}%`],
              ["Temperatura", formatMetric(robot.temperatureCelsius, "C")],
              ["CPU", formatMetric(robot.cpuUsage, "%")],
            ].map(([title, value]) => (
              <article key={title} className="rounded-[1.5rem] border border-white/15 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-sand/70">{title}</p>
                <p className="mt-2 font-display text-3xl">{value}</p>
              </article>
            ))}
          </div>
        </div>
      </article>
    </section>
  );
}
