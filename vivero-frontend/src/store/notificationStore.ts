import { create } from "zustand";

export type ToastItem = {
  id: string;
  title: string;
  variant: "info" | "critical";
};

type NotificationState = {
  toasts: ToastItem[];
  pushToast: (toast: ToastItem) => void;
  dismissToast: (id: string) => void;
};

export const useNotificationStore = create<NotificationState>((set) => ({
  toasts: [],
  pushToast: (toast) => set((state) => ({ toasts: [toast, ...state.toasts].slice(0, 4) })),
  dismissToast: (id) =>
    set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) })),
}));
