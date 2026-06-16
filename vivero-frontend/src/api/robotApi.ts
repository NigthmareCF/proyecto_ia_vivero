import api from "./axiosInstance";

export const getRobotStatus = () => api.get("/robot/status").then((res) => res.data.data);
export const startRobotPatrol = () =>
  api.post("/robot/command", { commandType: "START_PATROL" }).then((res) => res.data.data);
export const getRobotPatrolAnalysis = (patrolId: string) =>
  api.get(`/robot/patrols/${patrolId}/analysis`).then((res) => res.data.data);
export const getRobotPatrolObservations = (patrolId: string) =>
  api.get(`/robot/patrols/${patrolId}/observations`).then((res) => res.data.data);
export const finalizeRobotPatrolAnalysis = (patrolId: string, robotId = "ROBOT-001") =>
  api.post(`/robot/patrols/${patrolId}/analysis/finalize`, null, { params: { robotId } }).then((res) => res.data.data);

export type GenerateReportRequest = {
  patrolId: number;
  title: string;
  summary?: string;
  observationsCount: number;
  healthyCount: number;
  attentionCount: number;
  dangerCount: number;
  manualReviewCount: number;
  inconclusiveCount: number;
  plantDetails: Array<{
    plantGroupCode: string;
    finalState: string;
    summary?: string;
    findings: Array<{ side: string; note?: string }>;
  }>;
  analysisProvider?: string;
  analysisModel?: string;
  analysisNotes?: string;
};

export const createReport = (request: GenerateReportRequest) =>
  api.post("/reports", request).then((res) => res.data.data);

export type SearchStartOrientation = "FORWARD" | "REVERSE";
export type RobotSearchState = "SANO" | "ATENCION" | "PELIGRO" | "INCONCLUSA";
export type ManualDirection =
  | "FORWARD"
  | "BACKWARD"
  | "LEFT"
  | "RIGHT"
  | "FORWARD_RIGHT"
  | "FORWARD_LEFT"
  | "BACKWARD_RIGHT"
  | "BACKWARD_LEFT"
  | "STOP";

const manualDirections = new Set<ManualDirection>([
  "FORWARD",
  "BACKWARD",
  "LEFT",
  "RIGHT",
  "FORWARD_RIGHT",
  "FORWARD_LEFT",
  "BACKWARD_RIGHT",
  "BACKWARD_LEFT",
  "STOP",
]);
const speedProfileMap: Record<string, string> = {
  LOW: "LOW",
  MEDIUM: "MEDIUM",
  HIGH: "HIGH",
  TURBO: "TURBO",
};

function isManualDirection(command: string): command is ManualDirection {
  return manualDirections.has(command as ManualDirection);
}

export const sendRobotCommand = (command: string, value?: string | number) => {
  if (isManualDirection(command)) {
    return api
      .post("/robot/command", {
        commandType: "MANUAL_MOVE",
        direction: command,
        speed: typeof value === "number" ? value : typeof value === "string" ? Number(value) || 35 : 35,
      })
      .then((res) => res.data.data);
  }

  return api
    .post("/robot/command", {
      commandType: command,
      value,
    })
    .then((res) => res.data.data);
};

export const setRobotMode = (profile: "AUTO_LINE" | "MANUAL_FREE" | "ACRO") => {
  if (profile === "AUTO_LINE") {
    return api.post("/robot/command", { commandType: "SET_MODE", targetMode: "AUTO" }).then((res) => res.data.data);
  }
  if (profile === "MANUAL_FREE") {
    return api.post("/robot/command", { commandType: "SET_MODE", targetMode: "MANUAL" }).then((res) => res.data.data);
  }
  return api.post("/robot/command", { commandType: "RUN_ACRO", sequenceName: "SPIN" }).then((res) => res.data.data);
};

export const switchRobotCamera = (cameraName: "FRONT" | "LEFT" | "RIGHT") =>
  api.post("/robot/command", { commandType: "SWITCH_CAMERA", cameraName }).then((res) => res.data.data);

export const setRobotSpeedProfile = (speedProfile: "LOW" | "MEDIUM" | "HIGH" | "TURBO" | `CUSTOM_${number}`) =>
  api
    .post("/robot/command", {
      commandType: "SET_SPEED_PROFILE",
      speedProfile: speedProfileMap[speedProfile] ?? speedProfile,
    })
    .then((res) => res.data.data);

export const setRobotStreamProfile = (streamProfile: "VELOCIDAD" | "BALANCEADO" | "HD") =>
  api
    .post("/robot/command", {
      commandType: "SET_STREAM_PROFILE",
      streamProfile,
    })
    .then((res) => res.data.data);

export const goToRobotPlant = (targetPlantQr: string, searchStartOrientation: SearchStartOrientation = "FORWARD") =>
  api
    .post("/robot/command", {
      commandType: "GOTO_PLANT",
      targetPlantQr,
      searchStartOrientation,
    })
    .then((res) => res.data.data);

export const searchRobotByState = (
  requestedState: RobotSearchState,
  searchStartOrientation: SearchStartOrientation = "FORWARD",
) =>
  api
    .post("/robot/command", {
      commandType: "SEARCH_BY_STATE",
      requestedState,
      searchStartOrientation,
    })
    .then((res) => res.data.data);
