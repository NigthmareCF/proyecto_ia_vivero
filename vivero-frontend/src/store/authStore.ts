import { create } from "zustand";

export type AppRole = "ADMIN" | "CONTROLLER" | "VIEWER";

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
    return JSON.parse(localStorage.getItem("vivero-auth") ?? "{}");
  } catch {
    return {};
  }
})();

export function normalizeRole(role: unknown): AppRole | null {
  if (typeof role !== "string") return null;
  const normalized = role.trim().toUpperCase().replace(/^ROLE_/, "");
  if (normalized === "ADMIN" || normalized === "CONTROLLER" || normalized === "VIEWER") {
    return normalized;
  }
  return null;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: persisted.accessToken ?? null,
  refreshToken: persisted.refreshToken ?? null,
  fullName: persisted.fullName ?? null,
  email: persisted.email ?? null,
  role: normalizeRole(persisted.role),
  authProvider: persisted.authProvider ?? null,
  setSession: (payload) =>
    set((state) => {
      const next = { ...state, ...payload, role: normalizeRole(payload.role ?? state.role) };
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
