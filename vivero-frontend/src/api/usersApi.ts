import api from "./axiosInstance";

export const getUsers = () => api.get("/users").then((res) => res.data.data);
