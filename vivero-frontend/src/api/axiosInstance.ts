import axios from "axios";
import { useAuthStore } from "../store/authStore";
import { resolveApiBaseUrl } from "../utils/backendUrls";

const api = axios.create({
  baseURL: resolveApiBaseUrl(),
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const refreshToken = useAuthStore.getState().refreshToken;

    if (error.response?.status === 401 && refreshToken && !originalRequest._retry) {
      originalRequest._retry = true;
      const response = await axios.post(
        `${api.defaults.baseURL}/auth/refresh`,
        { refreshToken }
      );
      useAuthStore.getState().setSession(response.data.data);
      originalRequest.headers.Authorization = `Bearer ${response.data.data.accessToken}`;
      return api(originalRequest);
    }

    return Promise.reject(error);
  }
);

export default api;
