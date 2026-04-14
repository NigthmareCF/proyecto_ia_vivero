import { create } from "zustand";

type RobotState = {
  mode: string;
  batteryLevel: number;
  currentPlantQr: string | null;
  isConnected: boolean;
  setStatus: (status: Partial<RobotState>) => void;
};

export const useRobotStore = create<RobotState>((set) => ({
  mode: "IDLE",
  batteryLevel: 0,
  currentPlantQr: null,
  isConnected: false,
  setStatus: (status) => set((state) => ({ ...state, ...status })),
}));
