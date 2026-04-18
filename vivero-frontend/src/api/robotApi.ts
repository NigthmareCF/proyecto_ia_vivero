import api from "./axiosInstance";

export const getRobotStatus = () => api.get("/robot/status").then((res) => res.data.data);

const manualDirections = new Set(["FORWARD", "BACKWARD", "LEFT", "RIGHT", "STOP"]);
const speedProfileMap: Record<string, string> = {
  LOW: "LOW",
  MEDIUM: "MEDIUM",
  HIGH: "HIGH",
  TURBO: "TURBO",
};

export const sendRobotCommand = (command: string, value?: string) => {
  if (manualDirections.has(command)) {
    return api
      .post("/robot/command", {
        commandType: "MANUAL_MOVE",
        direction: command,
        speed: typeof value === "string" ? Number(value) || 35 : 35,
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

export const setRobotSpeedProfile = (speedProfile: "LOW" | "MEDIUM" | "HIGH" | "TURBO") =>
  api
    .post("/robot/command", { commandType: "SET_SPEED_PROFILE", speedProfile: speedProfileMap[speedProfile] })
    .then((res) => res.data.data);
