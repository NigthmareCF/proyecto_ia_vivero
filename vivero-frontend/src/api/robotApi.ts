import api from "./axiosInstance";

export const getRobotStatus = () => api.get("/robot/status").then((res) => res.data.data);
export const sendRobotCommand = (command: string, value?: string) =>
  api.post("/robot/command", { command, value }).then((res) => res.data.data);
