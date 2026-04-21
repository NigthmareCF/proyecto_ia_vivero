import api from "./axiosInstance";

export const getPlants = () => api.get("/plants").then((res) => res.data.data);
