import { useAuthStore } from "../store/authStore";

export function useAuth() {
  const auth = useAuthStore();
  return {
    ...auth,
    isAuthenticated: Boolean(auth.accessToken),
  };
}
