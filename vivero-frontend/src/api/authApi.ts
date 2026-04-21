import api from "./axiosInstance";

export const login = (email: string, password: string) =>
  api.post("/auth/login", { email, password }).then((res) => res.data.data);

export const register = (payload: {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  role: "CONTROLLER" | "VIEWER";
}) => api.post("/auth/register", payload).then((res) => res.data.data);

export const getMe = () => api.get("/auth/me").then((res) => res.data.data);
