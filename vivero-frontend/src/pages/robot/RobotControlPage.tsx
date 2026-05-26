import { useEffect, useRef, useState } from "react";
import {
  goToRobotPlant,
  RobotSearchState,
  SearchStartOrientation,
  searchRobotByState,
  sendRobotCommand,
  setRobotMode,
  setRobotSpeedProfile,
  switchRobotCamera,
} from "../../api/robotApi";
import { useNotificationStore } from "../../store/notificationStore";
import { useRobotStream } from "../../hooks/useRobotStream";
import { useRobotWebSocket } from "../../hooks/useRobotWebSocket";
import { useAuthStore } from "../../store/authStore";
import { useRobotStore } from "../../store/robotStore";

const commandLabels: Record<string, string> = {
  FORWARD: "Avanzar",
  BACKWARD: "Retroceder",
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

const movementHotkeys: Record<string, "FORWARD" | "BACKWARD" | "LEFT" | "RIGHT"> = {
  ArrowUp: "FORWARD",
  ArrowDown: "BACKWARD",
  ArrowLeft: "LEFT",
  ArrowRight: "RIGHT",
};

const standardProfileSpeed: Record<"LOW" | "MEDIUM" | "HIGH" | "TURBO", number> = {
  LOW: 30,
  MEDIUM: 45,
  HIGH: 65,
  TURBO: 85,
};

const orientationLabels: Record<SearchStartOrientation, string> = {
  FORWARD: "Mismo extremo",
  REVERSE: "Extremo opuesto",
};

const searchStates: RobotSearchState[] = ["ATENCION", "PELIGRO", "SANO", "INCONCLUSA"];

function formatMetric(value: number | null, suffix: string) {
  return value === null ? "--" : `${Math.round(value)}${suffix}`;
}

function resolveSpeedPercent(profile: string, fallback: number, customSpeed: number) {
  if (profile === "CUSTOM") return customSpeed;
  return standardProfileSpeed[profile as keyof typeof standardProfileSpeed] ?? fallback;
}

export function RobotControlPage() {
  const robot = useRobotStore();
  const role = useAuthStore((state) => state.role);
  const pushToast = useNotificationStore((state) => state.pushToast);
  const canDrive = role === "ADMIN" || role === "CONTROLLER";
  const canOperateRobot = canDrive && robot.isConnected;
  const isAdmin = role === "ADMIN";
  useRobotWebSocket();
  useRobotStream();

  const initialSpeed = robot.currentSpeedPercent ?? standardProfileSpeed.MEDIUM;
  const [selectedSpeedProfile, setSelectedSpeedProfile] = useState<string>(robot.speedProfile || "MEDIUM");
  const [customSpeedPercent, setCustomSpeedPercent] = useState<number>(initialSpeed);
  const [powerPanelOpen, setPowerPanelOpen] = useState(false);
  const [targetPlantQr, setTargetPlantQr] = useState("");
  const [searchState, setSearchState] = useState<RobotSearchState>("ATENCION");
  const [searchOrientation, setSearchOrientation] = useState<SearchStartOrientation>("FORWARD");
  const [isVideoFullscreen, setIsVideoFullscreen] = useState(false);
  const activeDirectionRef = useRef<"FORWARD" | "BACKWARD" | "LEFT" | "RIGHT" | null>(null);
  const commandIntervalRef = useRef<number | null>(null);
  const manualModeArmedRef = useRef(false);
  const streamContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (robot.speedProfile && robot.speedProfile !== selectedSpeedProfile && !selectedSpeedProfile.startsWith("CUSTOM")) {
      setSelectedSpeedProfile(robot.speedProfile);
    }
    if (robot.currentSpeedPercent !== null && selectedSpeedProfile !== "CUSTOM") {
      setCustomSpeedPercent(robot.currentSpeedPercent);
    }
  }, [robot.speedProfile, robot.currentSpeedPercent, selectedSpeedProfile]);

  useEffect(() => {
    return () => {
      if (commandIntervalRef.current !== null) {
        window.clearInterval(commandIntervalRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const onFullscreenChange = () => {
      setIsVideoFullscreen(document.fullscreenElement === streamContainerRef.current);
    };

    document.addEventListener("fullscreenchange", onFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", onFullscreenChange);
    };
  }, []);

  const activeSpeedPercent = resolveSpeedPercent(
    selectedSpeedProfile,
    robot.currentSpeedPercent ?? standardProfileSpeed.MEDIUM,
    customSpeedPercent,
  );

  const ensureRobotReady = (actionLabel: string) => {
    if (!canDrive) {
      pushToast({
        id: crypto.randomUUID(),
        title: "Tu rol actual no puede enviar comandos del robot",
        variant: "critical",
      });
      return false;
    }
    if (robot.isConnected) {
      return true;
    }
    pushToast({
      id: crypto.randomUUID(),
      title: `Robot sin conexion: no se puede ${actionLabel}`,
      variant: "critical",
    });
    return false;
  };

  const stopManualMotion = () => {
    activeDirectionRef.current = null;
    if (commandIntervalRef.current !== null) {
      window.clearInterval(commandIntervalRef.current);
      commandIntervalRef.current = null;
    }
    manualModeArmedRef.current = false;
    void sendRobotCommand("STOP", 0);
  };

  const ensureManualMode = async () => {
    if (manualModeArmedRef.current) return;
    if (!ensureRobotReady("activar modo manual")) return;
    manualModeArmedRef.current = true;
    await setRobotMode("MANUAL_FREE");
  };

  const dispatchManualMove = async (direction: "FORWARD" | "BACKWARD" | "LEFT" | "RIGHT") => {
    if (!ensureRobotReady("mover el robot")) return;
    await ensureManualMode();
    await sendRobotCommand(direction, activeSpeedPercent);
  };

  const startManualMotion = (direction: "FORWARD" | "BACKWARD" | "LEFT" | "RIGHT") => {
    if (!ensureRobotReady("mover el robot")) return;
    activeDirectionRef.current = direction;
    if (commandIntervalRef.current !== null) {
      window.clearInterval(commandIntervalRef.current);
    }
    void dispatchManualMove(direction);
    commandIntervalRef.current = window.setInterval(() => {
      if (activeDirectionRef.current) {
        void dispatchManualMove(activeDirectionRef.current);
      }
    }, 90);
  };

  const applyStandardProfile = (profile: "LOW" | "MEDIUM" | "HIGH" | "TURBO") => {
    if (!ensureRobotReady("cambiar potencia")) return;
    setSelectedSpeedProfile(profile);
    void setRobotSpeedProfile(profile);
  };

  const applyCustomProfile = () => {
    if (!ensureRobotReady("aplicar potencia custom")) return;
    setSelectedSpeedProfile("CUSTOM");
    void setRobotSpeedProfile(`CUSTOM_${customSpeedPercent}`);
    setPowerPanelOpen(false);
  };

  const submitGotoPlant = () => {
    if (!ensureRobotReady("ir a la planta")) return;
    const normalizedTarget = targetPlantQr.trim().toUpperCase();
    if (!normalizedTarget) return;
    stopManualMotion();
    void goToRobotPlant(normalizedTarget, searchOrientation);
  };

  const submitSearchByState = () => {
    if (!ensureRobotReady("buscar por estado")) return;
    stopManualMotion();
    void searchRobotByState(searchState, searchOrientation);
  };

  const toggleVideoFullscreen = async () => {
    const container = streamContainerRef.current;
    if (!container) return;
    if (document.fullscreenElement === container) {
      await document.exitFullscreen();
      return;
    }
    await container.requestFullscreen();
  };

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.repeat && !movementHotkeys[event.key]) {
        return;
      }

      if (powerPanelOpen && isAdmin) {
        if (event.key === "Escape") {
          setPowerPanelOpen(false);
          return;
        }
        if (event.key === "ArrowLeft") {
          event.preventDefault();
          setCustomSpeedPercent((current) => Math.max(0, current - 5));
          return;
        }
        if (event.key === "ArrowRight") {
          event.preventDefault();
          setCustomSpeedPercent((current) => Math.min(100, current + 5));
          return;
        }
        if (event.key === "Enter") {
          event.preventDefault();
          applyCustomProfile();
          return;
        }
      }

      if (cameraHotkeys[event.key]) {
        if (!ensureRobotReady("cambiar camara")) return;
        void switchRobotCamera(cameraHotkeys[event.key]);
        return;
      }

      const lowerKey = event.key.toLowerCase();
      if (lowerKey === "m") {
        if (!ensureRobotReady("activar modo manual")) return;
        void setRobotMode("MANUAL_FREE");
        return;
      }
      if (lowerKey === "a") {
        if (!ensureRobotReady("activar modo automatico")) return;
        stopManualMotion();
        void setRobotMode("AUTO_LINE");
        return;
      }
      if (lowerKey === "x") {
        if (!ensureRobotReady("ejecutar acrobacia")) return;
        stopManualMotion();
        void setRobotMode("ACRO");
        return;
      }
      if (speedHotkeys[lowerKey] && canOperateRobot) {
        applyStandardProfile(speedHotkeys[lowerKey]);
        return;
      }
      if (lowerKey === "p" && isAdmin) {
        setPowerPanelOpen((current) => !current);
        return;
      }

      const direction = movementHotkeys[event.key];
      if (direction && canDrive) {
        event.preventDefault();
        if (activeDirectionRef.current !== direction) {
          startManualMotion(direction);
        }
      }
    };

    const onKeyUp = (event: KeyboardEvent) => {
      const direction = movementHotkeys[event.key];
      if (direction && activeDirectionRef.current === direction) {
        event.preventDefault();
        stopManualMotion();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
    };
  }, [activeSpeedPercent, canDrive, customSpeedPercent, isAdmin, powerPanelOpen]);

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
          <span className="rounded-full bg-sand px-3 py-1">Potencia {selectedSpeedProfile}</span>
          <span className="rounded-full bg-sand px-3 py-1">PWM {activeSpeedPercent}%</span>
          <span className="rounded-full bg-sand px-3 py-1">QR {robot.currentPlantQr ?? "sin objetivo"}</span>
          <span className="inline-flex items-center gap-2 rounded-full bg-sand px-3 py-1">
            <span className={`h-2.5 w-2.5 rounded-full ${connectionClass}`} />
            {robot.isConnected ? robot.connectionQuality : "OFFLINE"}
          </span>
        </div>

        <p className="mt-4 text-sm text-moss">{robot.statusSummary}</p>
        {!robot.isConnected ? (
          <p className="mt-2 text-sm text-alert">
            El runtime del robot esta offline. Los comandos manuales, auto y acro quedaran bloqueados hasta reconectar.
          </p>
        ) : null}
        {robot.lastWatchdogReason ? (
          <p className="mt-2 text-sm text-alert">Ultimo corte defensivo: {robot.lastWatchdogReason}</p>
        ) : null}

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

        <div className="mt-4 grid gap-3 sm:grid-cols-4">
          <article className="rounded-[1.5rem] border border-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Cola local</p>
            <p className="mt-2 font-display text-3xl text-ink">{robot.queueDepth}</p>
          </article>
          <article className="rounded-[1.5rem] border border-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Stream</p>
            <p className="mt-2 font-display text-3xl text-ink">{robot.streamActive ? "Activo" : "Inactivo"}</p>
          </article>
          <article className="rounded-[1.5rem] border border-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Obstaculo frontal</p>
            <p className={`mt-2 font-display text-3xl ${robot.obstacleDetected ? "text-alert" : "text-ink"}`}>
              {robot.obstacleDetected ? "Detectado" : "Libre"}
            </p>
          </article>
          <article className="rounded-[1.5rem] border border-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Obstaculo trasero</p>
            <p className={`mt-2 font-display text-3xl ${robot.rearObstacleDetected ? "text-alert" : "text-ink"}`}>
              {robot.rearObstacleDetected ? "Bloquea reversa" : "Libre"}
            </p>
          </article>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3">
          {["FORWARD", "BACKWARD", "LEFT", "RIGHT", "STOP"].map((command) => (
            <button
              key={command}
              className="rounded-2xl bg-ink px-4 py-3 text-white transition hover:bg-clay disabled:cursor-not-allowed disabled:bg-stone-400"
              disabled={!canOperateRobot}
              onMouseDown={() => {
                if (command === "STOP") {
                  stopManualMotion();
                  return;
                }
                startManualMotion(command as "FORWARD" | "BACKWARD" | "LEFT" | "RIGHT");
              }}
              onMouseUp={() => {
                if (command !== "STOP") stopManualMotion();
              }}
              onMouseLeave={() => {
                if (command !== "STOP" && activeDirectionRef.current === command) stopManualMotion();
              }}
              onClick={() => {
                if (command === "STOP") {
                  stopManualMotion();
                }
              }}
            >
              {commandLabels[command] ?? command}
            </button>
          ))}
        </div>

        <div className="mt-6 flex flex-wrap gap-2">
          {(["LOW", "MEDIUM", "HIGH", "TURBO"] as const).map((profile) => (
            <button
              key={profile}
              className={`rounded-full px-4 py-2 text-sm transition ${
                selectedSpeedProfile === profile ? "bg-ink text-white" : "bg-sand text-ink hover:bg-clay hover:text-white"
              }`}
              disabled={!canOperateRobot}
              onClick={() => applyStandardProfile(profile)}
            >
              {profile} {standardProfileSpeed[profile]}%
            </button>
          ))}
          {isAdmin ? (
            <button
              className={`rounded-full px-4 py-2 text-sm transition ${
                selectedSpeedProfile === "CUSTOM" ? "bg-clay text-white" : "bg-sand text-ink hover:bg-clay hover:text-white"
              }`}
              disabled={!robot.isConnected}
              onClick={() => setPowerPanelOpen(true)}
            >
              CUSTOM {customSpeedPercent}%
            </button>
          ) : null}
        </div>

        <div className="mt-6 rounded-[1.5rem] border border-sand p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-moss">Busqueda guiada</p>
              <p className="mt-1 text-sm text-moss">
                Define si el robot arranca desde el mismo extremo historico o desde el extremo opuesto.
              </p>
            </div>
            <span className="rounded-full bg-sand px-3 py-1 text-sm text-ink">Orientacion {searchOrientation}</span>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {(["FORWARD", "REVERSE"] as const).map((orientation) => (
              <button
                key={orientation}
                className={`rounded-full px-4 py-2 text-sm transition ${
                  searchOrientation === orientation
                    ? "bg-ink text-white"
                    : "bg-sand text-ink hover:bg-clay hover:text-white"
                }`}
                disabled={!canOperateRobot}
                onClick={() => setSearchOrientation(orientation)}
              >
                {orientationLabels[orientation]}
              </button>
            ))}
          </div>

          <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_auto]">
            <input
              value={targetPlantQr}
              onChange={(event) => setTargetPlantQr(event.target.value.toUpperCase())}
              placeholder="PLA_12_MA_7_IZ o PLA_12_MA_7"
              className="rounded-2xl border border-sand px-4 py-3 text-sm text-ink outline-none transition focus:border-clay"
            />
            <button
              className="rounded-2xl bg-ink px-5 py-3 text-white transition hover:bg-clay disabled:cursor-not-allowed disabled:bg-stone-400"
              disabled={!canOperateRobot || targetPlantQr.trim().length === 0}
              onClick={submitGotoPlant}
            >
              Ir a planta
            </button>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {searchStates.map((stateOption) => (
              <button
                key={stateOption}
                className={`rounded-full px-4 py-2 text-sm transition ${
                  searchState === stateOption ? "bg-clay text-white" : "bg-sand text-ink hover:bg-clay hover:text-white"
                }`}
                disabled={!canOperateRobot}
                onClick={() => setSearchState(stateOption)}
              >
                {stateOption}
              </button>
            ))}
            <button
              className="rounded-full bg-ink px-4 py-2 text-sm text-white transition hover:bg-clay disabled:cursor-not-allowed disabled:bg-stone-400"
              disabled={!canOperateRobot}
              onClick={submitSearchByState}
            >
              Buscar por estado
            </button>
          </div>
        </div>
      </article>

      <article className="rounded-[2rem] bg-ink p-6 text-sand shadow-sm">
        <h2 className="font-display text-3xl">Camara y estado</h2>
        <div className="mt-4 grid gap-4">
          <div
            ref={streamContainerRef}
            className={`relative grid place-items-center overflow-hidden rounded-[1.5rem] border border-white/20 bg-white/5 ${
              isVideoFullscreen ? "min-h-screen rounded-none border-0 bg-black" : "min-h-80"
            }`}
          >
            <div className="absolute inset-x-0 top-0 flex items-center justify-between bg-gradient-to-b from-black/45 to-transparent px-4 py-3 text-xs uppercase tracking-[0.18em] text-sand">
              <span>Recorrido en vivo</span>
              <div className="flex items-center gap-3">
                <span>{robot.activeCamera} · {robot.streamActive ? "stream activo" : "stream en espera"}</span>
                <button
                  type="button"
                  className="rounded-full border border-white/30 bg-black/20 px-3 py-1 text-[11px] text-white transition hover:bg-white/15"
                  onClick={() => {
                    void toggleVideoFullscreen();
                  }}
                >
                  {isVideoFullscreen ? "Salir pantalla completa" : "Pantalla completa"}
                </button>
                {isVideoFullscreen ? <p className="mt-2 text-sm text-sand/70">Presiona `Esc` para salir.</p> : null}
              </div>
            </div>
            {robot.latestStreamFrameUrl ? (
              <img
                src={robot.latestStreamFrameUrl}
                alt={`Stream ${robot.latestStreamCamera ?? robot.activeCamera}`}
                className={`w-full object-cover ${isVideoFullscreen ? "h-screen" : "h-full min-h-80"}`}
              />
            ) : (
              <div className="text-center">
                <p className="font-display text-4xl">{robot.streamActive ? robot.activeCamera : "Sin video"}</p>
                <p className="mt-2 text-sm text-sand/70">
                  `1/2/3` camaras · flechas para manejo manual · `A/M/X` perfiles de control
                </p>
              </div>
            )}
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <article className="rounded-[1.5rem] border border-white/15 bg-white/5 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-sand/70">Atajos</p>
              <p className="mt-3 text-sm leading-6 text-sand/85">
                Flechas: mover · soltar tecla: detener · `Q/W/E/R`: baja/media/alta/turbo
              </p>
              <p className="mt-2 text-sm leading-6 text-sand/85">
                `P`: potencia custom admin · `1/2/3`: camaras · `A/M/X`: auto/manual/acro
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

      {powerPanelOpen && isAdmin ? (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-[2rem] bg-white p-6 shadow-2xl">
            <h3 className="font-display text-3xl text-ink">Potencia custom</h3>
            <p className="mt-2 text-sm text-moss">
              Ajusta con flechas izquierda/derecha o con los botones. `Enter` aplica y `Escape` cierra.
            </p>
            <div className="mt-6 rounded-[1.5rem] bg-sand p-5 text-center">
              <p className="text-xs uppercase tracking-[0.18em] text-moss">PWM actual</p>
              <p className="mt-2 font-display text-5xl text-ink">{customSpeedPercent}%</p>
            </div>
            <div className="mt-5 flex items-center justify-center gap-3">
              <button
                className="rounded-full bg-sand px-4 py-2 text-ink transition hover:bg-clay hover:text-white"
                onClick={() => setCustomSpeedPercent((current) => Math.max(0, current - 5))}
              >
                -5
              </button>
              <button
                className="rounded-full bg-sand px-4 py-2 text-ink transition hover:bg-clay hover:text-white"
                onClick={() => setCustomSpeedPercent((current) => Math.min(100, current + 5))}
              >
                +5
              </button>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button
                className="rounded-full border border-sand px-4 py-2 text-ink transition hover:bg-sand"
                onClick={() => setPowerPanelOpen(false)}
              >
                Cerrar
              </button>
              <button className="rounded-full bg-ink px-5 py-2 text-white transition hover:bg-clay" onClick={applyCustomProfile}>
                Aplicar
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
