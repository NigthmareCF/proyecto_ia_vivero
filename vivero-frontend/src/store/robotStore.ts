import { create } from "zustand";

export type RobotConnectionQuality = "EXCELLENT" | "GOOD" | "FAIR" | "WEAK" | "OFFLINE" | string;

export type RobotState = {
  mode: string;
  batteryLevel: number;
  temperatureCelsius: number | null;
  cpuUsage: number | null;
  connectionQuality: RobotConnectionQuality;
  obstacleDetected: boolean;
  streamActive: boolean;
  queueDepth: number;
  statusSummary: string;
  activeCamera: string;
  controlProfile: string;
  speedProfile: string;
  currentSpeedPercent: number | null;
  currentPlantQr: string | null;
  rearObstacleDetected: boolean;
  lastWatchdogReason: string | null;
  latestStreamFrameUrl: string | null;
  latestStreamCamera: string | null;
  latestStreamFrameAt: string | null;
  streamSocketConnected: boolean;
  isConnected: boolean;
  setStatus: (status: Partial<RobotState>) => void;
};

export const initialRobotState: Omit<RobotState, "setStatus"> = {
  mode: "IDLE",
  batteryLevel: 0,
  temperatureCelsius: null,
  cpuUsage: null,
  connectionQuality: "OFFLINE",
  obstacleDetected: false,
  streamActive: false,
  queueDepth: 0,
  statusSummary: "Sin telemetria disponible.",
  activeCamera: "FRONT",
  controlProfile: "IDLE",
  speedProfile: "MEDIUM",
  currentSpeedPercent: null,
  currentPlantQr: null,
  rearObstacleDetected: false,
  lastWatchdogReason: null,
  latestStreamFrameUrl: null,
  latestStreamCamera: null,
  latestStreamFrameAt: null,
  streamSocketConnected: false,
  isConnected: false,
};

const toNumber = (value: unknown): number | null => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
};

const toBoolean = (value: unknown): boolean | null => {
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return value !== 0;
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["true", "1", "yes", "si", "active", "on"].includes(normalized)) return true;
    if (["false", "0", "no", "inactive", "off"].includes(normalized)) return false;
  }
  return null;
};

const toText = (value: unknown): string | null => {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
};

export function normalizeRobotStatus(payload: unknown): Partial<RobotState> {
  const source = payload && typeof payload === "object" ? (payload as Record<string, unknown>) : {};

  const mode =
    toText(source.mode) ??
    toText(source.status) ??
    toText(source.robotMode) ??
    toText(source.robot_mode) ??
    undefined;

  const batteryLevel =
    toNumber(source.batteryLevel) ??
    toNumber(source.battery) ??
    toNumber(source.battery_level) ??
    undefined;

  const temperatureCelsius =
    toNumber(source.temperatureCelsius) ??
    toNumber(source.temperature) ??
    toNumber(source.temperature_celsius) ??
    toNumber(source.cpuTemperature) ??
    toNumber(source.cpu_temperature);

  const cpuUsage =
    toNumber(source.cpuUsage) ??
    toNumber(source.cpuUsagePercent) ??
    toNumber(source.cpu) ??
    toNumber(source.cpu_usage) ??
    toNumber(source.cpu_usage_percent) ??
    toNumber(source.cpuLoad) ??
    toNumber(source.cpu_load);

  const connectionQuality =
    toText(source.connectionQuality) ??
    toText(source.connection_quality) ??
    toText(source.connection) ??
    undefined;

  const obstacleDetected =
    toBoolean(source.obstacleDetected) ??
    toBoolean(source.obstacle_detected) ??
    toBoolean(source.obstacle) ??
    toBoolean(source.pathBlocked) ??
    toBoolean(source.path_blocked) ??
    undefined;

  const streamActive =
    toBoolean(source.streamActive) ??
    toBoolean(source.stream_active) ??
    toBoolean(source.videoActive) ??
    toBoolean(source.video_active) ??
    undefined;

  const queueDepth =
    toNumber(source.queueDepth) ??
    toNumber(source.queue_depth) ??
    toNumber(source.pendingUploads) ??
    toNumber(source.pending_uploads) ??
    undefined;

  const statusSummary =
    toText(source.statusSummary) ??
    toText(source.status_summary) ??
    toText(source.summary) ??
    toText(source.message) ??
    undefined;

  const activeCamera =
    toText(source.activeCamera) ??
    toText(source.active_camera) ??
    toText(source.camera) ??
    undefined;

  const controlProfile =
    toText(source.controlProfile) ??
    toText(source.control_profile) ??
    undefined;

  const speedProfile =
    toText(source.speedProfile) ??
    toText(source.speed_profile) ??
    undefined;

  const currentPlantQr =
    toText(source.currentPlantQr) ??
    toText(source.current_plant_qr) ??
    toText(source.plantQr) ??
    toText(source.plant_qr) ??
    null;

  const currentSpeedPercent =
    toNumber(source.currentSpeedPercent) ??
    toNumber(source.current_speed_percent) ??
    null;

  const rearObstacleDetected =
    toBoolean(source.rearObstacleDetected) ??
    toBoolean(source.rear_obstacle_detected) ??
    undefined;

  const lastWatchdogReason =
    toText(source.lastWatchdogReason) ??
    toText(source.last_watchdog_reason) ??
    null;

  const latestStreamFrameUrl =
    toText(source.latestStreamFrameUrl) ??
    toText(source.latest_stream_frame_url) ??
    null;

  const latestStreamCamera =
    toText(source.latestStreamCamera) ??
    toText(source.latest_stream_camera) ??
    null;

  const isConnected = toBoolean(source.isConnected) ?? toBoolean(source.is_connected) ?? undefined;

  return {
    ...(mode ? { mode } : {}),
    ...(batteryLevel !== undefined ? { batteryLevel } : {}),
    ...(temperatureCelsius !== null ? { temperatureCelsius } : {}),
    ...(cpuUsage !== null ? { cpuUsage } : {}),
    ...(connectionQuality ? { connectionQuality } : {}),
    ...(obstacleDetected !== undefined ? { obstacleDetected } : {}),
    ...(streamActive !== undefined ? { streamActive } : {}),
    ...(queueDepth !== undefined ? { queueDepth } : {}),
    ...(statusSummary ? { statusSummary } : {}),
    ...(activeCamera ? { activeCamera } : {}),
    ...(controlProfile ? { controlProfile } : {}),
    ...(speedProfile ? { speedProfile } : {}),
    ...(currentSpeedPercent !== null ? { currentSpeedPercent } : {}),
    ...(currentPlantQr ? { currentPlantQr } : {}),
    ...(rearObstacleDetected !== undefined ? { rearObstacleDetected } : {}),
    ...(lastWatchdogReason ? { lastWatchdogReason } : {}),
    ...(latestStreamFrameUrl ? { latestStreamFrameUrl } : {}),
    ...(latestStreamCamera ? { latestStreamCamera } : {}),
    ...(isConnected !== undefined ? { isConnected } : {}),
  };
}

export const useRobotStore = create<RobotState>((set) => ({
  ...initialRobotState,
  setStatus: (status) => set((state) => ({ ...state, ...status })),
}));
