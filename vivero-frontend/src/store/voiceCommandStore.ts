import { create } from "zustand";

export type VoiceCommandStatus = "idle" | "listening" | "processing" | "unsupported" | "error";

type VoiceCommandState = {
  enabled: boolean;
  supported: boolean;
  status: VoiceCommandStatus;
  transcript: string;
  lastAction: string | null;
  errorMessage: string | null;
  setEnabled: (enabled: boolean) => void;
  setSupported: (supported: boolean) => void;
  setStatus: (status: VoiceCommandStatus) => void;
  setTranscript: (transcript: string) => void;
  setLastAction: (lastAction: string | null) => void;
  setErrorMessage: (errorMessage: string | null) => void;
};

const persisted = (() => {
  try {
    return JSON.parse(localStorage.getItem("vivero-voice-command") ?? "{}");
  } catch {
    return {};
  }
})();

export const useVoiceCommandStore = create<VoiceCommandState>((set) => ({
  enabled: Boolean(persisted.enabled),
  supported: persisted.supported ?? true,
  status: persisted.supported === false ? "unsupported" : "idle",
  transcript: "",
  lastAction: null,
  errorMessage: null,
  setEnabled: (enabled) =>
    set((state) => {
      localStorage.setItem("vivero-voice-command", JSON.stringify({ ...persisted, enabled, supported: state.supported }));
      return { enabled };
    }),
  setSupported: (supported) =>
    set((state) => {
      localStorage.setItem("vivero-voice-command", JSON.stringify({ ...persisted, enabled: state.enabled, supported }));
      return { supported };
    }),
  setStatus: (status) => set({ status }),
  setTranscript: (transcript) => set({ transcript }),
  setLastAction: (lastAction) => set({ lastAction }),
  setErrorMessage: (errorMessage) => set({ errorMessage }),
}));
