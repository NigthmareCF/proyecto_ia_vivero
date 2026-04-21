import api from "./axiosInstance";

export const getReports = () => api.get("/reports").then((res) => res.data.data);
export const getNotificationConfigs = () =>
  api.get("/reports/notifications/config").then((res) => res.data.data);
