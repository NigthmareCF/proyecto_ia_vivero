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
    const status = error.response?.status;
    const canTryRefresh =
      (status === 401 || status === 403) &&
      refreshToken &&
      originalRequest &&
      !originalRequest._retry &&
      !String(originalRequest.url ?? "").includes("/auth/refresh");

    if (canTryRefresh) {
      originalRequest._retry = true;
      try {
        const response = await axios.post(
          `${api.defaults.baseURL}/auth/refresh`,
          { refreshToken }
        );
        useAuthStore.getState().setSession(response.data.data);
        originalRequest.headers = originalRequest.headers ?? {};
        originalRequest.headers.Authorization = `Bearer ${response.data.data.accessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        useAuthStore.getState().clear();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
