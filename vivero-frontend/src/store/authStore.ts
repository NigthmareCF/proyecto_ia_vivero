import { create } from "zustand";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  fullName: string | null;
  email: string | null;
  role: string | null;
  authProvider: string | null;
  setSession: (payload: Partial<AuthState>) => void;
  clear: () => void;
};

const persisted = (() => {
  try {
    const value = JSON.parse(localStorage.getItem("vivero-auth") ?? "{}");
    if (!value || typeof value !== "object") {
      localStorage.removeItem("vivero-auth");
      return {};
    }
    return value;
  } catch {
    localStorage.removeItem("vivero-auth");
    return {};
  }
})();

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: persisted.accessToken ?? null,
  refreshToken: persisted.refreshToken ?? null,
  fullName: persisted.fullName ?? null,
  email: persisted.email ?? null,
  role: persisted.role ?? null,
  authProvider: persisted.authProvider ?? null,
  setSession: (payload) =>
    set((state) => {
      const next = { ...state, ...payload };
      localStorage.setItem("vivero-auth", JSON.stringify(next));
      return next;
    }),
  clear: () =>
    set(() => {
      localStorage.removeItem("vivero-auth");
      return {
        accessToken: null,
        refreshToken: null,
        fullName: null,
        email: null,
        role: null,
        authProvider: null,
      };
    }),
}));
