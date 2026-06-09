import api from "./axiosInstance";

export const getReports = () => api.get("/reports").then((res) => res.data.data);
export const getNotificationConfigs = () =>
  api.get("/reports/notifications/config").then((res) => res.data.data);

export const getReportPdf = (reportId: number) =>
  api.get(`/reports/${reportId}/pdf`, { responseType: "blob" }).then((res) => res.data as Blob);

export const notifyReport = (reportId: number) =>
  api.post("/reports/notify", { reportId }).then((res) => res.data.data);
