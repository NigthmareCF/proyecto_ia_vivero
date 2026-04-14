import api from "./axiosInstance";

export const login = (email: string, password: string) =>
  api.post("/auth/login", { email, password }).then((res) => res.data.data);

export const socialLogin = (provider: "GOOGLE" | "APPLE", idToken: string) =>
  api.post("/auth/social", { provider, idToken }).then((res) => res.data.data);

export const getMe = () => api.get("/auth/me").then((res) => res.data.data);
