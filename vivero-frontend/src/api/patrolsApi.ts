import api from "./axiosInstance";

export const getPatrols = () => api.get("/patrols").then((res) => res.data.data);
