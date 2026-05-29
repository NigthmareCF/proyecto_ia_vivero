import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  goToRobotPlant,
  searchRobotByState,
  sendRobotCommand,
  setRobotMode,
  setRobotSpeedProfile,
  switchRobotCamera,
} from "../../api/robotApi";
import { useNotificationStore } from "../../store/notificationStore";
import { useRobotStore } from "../../store/robotStore";
import { useVoiceCommandStore } from "../../store/voiceCommandStore";
import { parseVoiceCommandSequence, type ParsedVoiceCommand } from "../../utils/voiceCommands";

type SpeechRecognitionAlternative = {
  transcript: string;
};

type SpeechRecognitionResult = {
  isFinal: boolean;
  0: SpeechRecognitionAlternative;
};

type SpeechRecognitionEventLike = Event & {
  resultIndex: number;
  results: ArrayLike<SpeechRecognitionResult>;
};

type SpeechRecognitionErrorEventLike = Event & {
  error: string;
};

type SpeechRecognitionInstance = EventTarget & {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onstart: ((event: Event) => void) | null;
  onend: ((event: Event) => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
};

type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;

function resolveRecognitionConstructor(): SpeechRecognitionConstructor | null {
  const api = (window.SpeechRecognition || window.webkitSpeechRecognition) as SpeechRecognitionConstructor | undefined;
  return api ?? null;
}

function resolveCommandErrorMessage(error: unknown) {
  if (typeof error === "object" && error !== null) {
    const axiosError = error as {
      response?: {
        status?: number;
        data?: {
          message?: string;
          error?: string;
        };
      };
      message?: string;
    };
    if (axiosError.response?.status === 403) {
      return "Tu rol actual no puede ejecutar comandos del robot";
    }
    const apiMessage = axiosError.response?.data?.message;
    if (apiMessage) {
      return apiMessage;
    }
    if (axiosError.message) {
      return axiosError.message;
    }
  }
  return "Error ejecutando comando de voz";
}

export function VoiceCommandDock() {
  const navigate = useNavigate();
  const location = useLocation();
  const pushToast = useNotificationStore((state) => state.pushToast);
  const robot = useRobotStore();
  const {
    enabled,
    supported,
    status,
    transcript,
    lastAction,
    errorMessage,
    setEnabled,
    setSupported,
    setStatus,
    setTranscript,
    setLastAction,
    setErrorMessage,
  } = useVoiceCommandStore();
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const shouldRestartRef = useRef(false);
  const enabledRef = useRef(enabled);
  const pathnameRef = useRef(location.pathname);
  const restartTimeoutRef = useRef<number | null>(null);
  const commandQueueRef = useRef<ParsedVoiceCommand[]>([]);
  const isExecutingRef = useRef(false);
  const lastHandledPhraseRef = useRef<{ value: string; at: number } | null>(null);
  const scheduleRecognitionRestartRef = useRef<(() => void) | null>(null);
  const recognitionActiveRef = useRef(false);
  const [, setQueuedTick] = useState(0);

  useEffect(() => {
    enabledRef.current = enabled;
    shouldRestartRef.current = enabled;
  }, [enabled]);

  useEffect(() => {
    pathnameRef.current = location.pathname;
  }, [location.pathname]);

  const bumpQueueTick = () => setQueuedTick((current) => current + 1);

  useEffect(() => {
    const RecognitionCtor = resolveRecognitionConstructor();
    if (!RecognitionCtor) {
      setSupported(false);
      setStatus("unsupported");
      return;
    }

    setSupported(true);
    const recognition = new RecognitionCtor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "es-ES";

    const clearPendingRestart = () => {
      if (restartTimeoutRef.current !== null) {
        window.clearTimeout(restartTimeoutRef.current);
        restartTimeoutRef.current = null;
      }
    };

    const startRecognitionSafely = () => {
      if (!enabledRef.current) {
        return;
      }
      if (recognitionActiveRef.current) {
        return;
      }
      try {
        recognition.start();
      } catch {
        try {
          recognition.stop();
        } catch {
          // Ignorado.
        }
      }
    };

    const scheduleRecognitionRestart = () => {
      if (!enabledRef.current) {
        setStatus("idle");
        return;
      }
      clearPendingRestart();
      setStatus("idle");
      restartTimeoutRef.current = window.setTimeout(() => {
        restartTimeoutRef.current = null;
        if (!enabledRef.current) {
          return;
        }
        try {
          recognition.stop();
        } catch {
          // Ignorado: algunos navegadores lanzan si ya está detenido.
        }
        startRecognitionSafely();
      }, 250);
    };
    scheduleRecognitionRestartRef.current = scheduleRecognitionRestart;

    const executeCommand = async (parsedCommand: ParsedVoiceCommand) => {
      if (pathnameRef.current !== parsedCommand.path) {
        navigate(parsedCommand.path);
      }

      switch (parsedCommand.kind) {
        case "navigate":
          break;
        case "robot_mode":
          await setRobotMode(parsedCommand.mode);
          break;
        case "robot_stop":
          await sendRobotCommand("STOP", 0);
          break;
        case "robot_move":
          await setRobotMode("MANUAL_FREE");
          await sendRobotCommand(parsedCommand.direction, robot.currentSpeedPercent ?? 45);
          break;
        case "robot_camera":
          await switchRobotCamera(parsedCommand.camera);
          break;
        case "robot_search_state":
          await searchRobotByState(parsedCommand.state, parsedCommand.orientation);
          break;
        case "robot_goto":
          await goToRobotPlant(parsedCommand.targetPlantQr, parsedCommand.orientation);
          break;
        case "robot_speed":
          await setRobotSpeedProfile(parsedCommand.profile);
          break;
        case "robot_speed_custom":
          await setRobotSpeedProfile(`CUSTOM_${parsedCommand.percent}`);
          break;
      }
    };

    const processQueuedCommands = async () => {
      if (isExecutingRef.current) {
        return;
      }

      isExecutingRef.current = true;
      while (commandQueueRef.current.length > 0) {
        const nextCommand = commandQueueRef.current.shift();
        bumpQueueTick();
        if (!nextCommand) {
          continue;
        }

        setLastAction(nextCommand.summary);
        try {
          await executeCommand(nextCommand);
          pushToast({
            id: crypto.randomUUID(),
            title: `Voz: ${nextCommand.summary}`,
            variant: "info",
          });
        } catch (error) {
          const message = resolveCommandErrorMessage(error);
          setErrorMessage(message);
          pushToast({
            id: crypto.randomUUID(),
            title: `Voz: ${message}`,
            variant: "critical",
          });
        }
      }
      isExecutingRef.current = false;
      if (enabledRef.current) {
        setStatus("listening");
      }
    };

    recognition.onstart = () => {
      recognitionActiveRef.current = true;
      setStatus("listening");
      setErrorMessage(null);
    };

    recognition.onend = () => {
      recognitionActiveRef.current = false;
      if (shouldRestartRef.current) {
        scheduleRecognitionRestart();
        return;
      }
      setStatus("idle");
    };

    recognition.onerror = (event) => {
      recognitionActiveRef.current = false;
      if (event.error === "aborted") {
        if (enabledRef.current) {
          scheduleRecognitionRestart();
        } else {
          setStatus("idle");
        }
        return;
      }
      setStatus("error");
      setErrorMessage(`Reconocimiento de voz: ${event.error}`);
      scheduleRecognitionRestart();
    };

    recognition.onresult = async (event) => {
      const latest = event.results[event.results.length - 1];
      const spokenText = latest?.[0]?.transcript?.trim() ?? "";
      if (!spokenText) {
        return;
      }
      setTranscript(spokenText);
      if (!latest.isFinal) {
        return;
      }

      const dedupeKey = spokenText.trim().toLowerCase();
      const now = Date.now();
      if (
        lastHandledPhraseRef.current &&
        lastHandledPhraseRef.current.value === dedupeKey &&
        now - lastHandledPhraseRef.current.at < 1200
      ) {
        return;
      }
      lastHandledPhraseRef.current = { value: dedupeKey, at: now };

      const parsedCommands = parseVoiceCommandSequence(spokenText);
      if (parsedCommands.length === 0) {
        setLastAction("Comando no reconocido");
        pushToast({
          id: crypto.randomUUID(),
          title: `Voz no reconocida: ${spokenText}`,
          variant: "info",
        });
        return;
      }

      commandQueueRef.current.push(...parsedCommands);
      bumpQueueTick();
      setLastAction(
        parsedCommands.length > 1
          ? `En cola ${parsedCommands.length} comandos de voz`
          : `En cola: ${parsedCommands[0].summary}`,
      );
      if (parsedCommands.length > 1) {
        pushToast({
          id: crypto.randomUUID(),
          title: `Voz: ${parsedCommands.length} comandos en cola`,
          variant: "info",
        });
      }
      void processQueuedCommands();
    };

    recognitionRef.current = recognition;
    return () => {
      shouldRestartRef.current = false;
      scheduleRecognitionRestartRef.current = null;
      recognitionActiveRef.current = false;
      clearPendingRestart();
      recognition.stop();
      recognitionRef.current = null;
    };
  }, [
    navigate,
    pushToast,
    robot.currentSpeedPercent,
    setErrorMessage,
    setLastAction,
    setStatus,
    setSupported,
    setTranscript,
  ]);

  useEffect(() => {
    const recognition = recognitionRef.current;
    if (!recognition || !supported) {
      return;
    }

    if (enabled) {
      scheduleRecognitionRestartRef.current?.();
      return;
    }
    recognitionActiveRef.current = false;
    recognition.stop();
    setStatus("idle");
  }, [enabled, supported]);

  useEffect(() => {
    if (!enabled || !supported) {
      return;
    }
    scheduleRecognitionRestartRef.current?.();
  }, [enabled, location.pathname, supported]);

  const toggleVoiceControl = () => {
    setEnabled(!enabled);
    setErrorMessage(null);
    if (enabled) {
      setStatus("idle");
      return;
    }
    setTranscript("");
  };

  const statusLabel =
    status === "unsupported"
      ? "Sin soporte"
      : status === "listening"
        ? "Escuchando"
        : status === "error"
            ? "Error"
            : "En espera";

  const indicatorClass =
    status === "listening"
      ? "bg-emerald-500"
      : status === "error"
          ? "bg-rose-500"
          : "bg-stone-400";

  return (
    <section className="rounded-[2rem] bg-white/80 p-4 shadow-sm backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-moss">Voz global</p>
          <h2 className="font-display text-2xl text-ink">Control por voz</h2>
        </div>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full bg-sand px-3 py-1 text-sm text-ink">
            <span className={`h-2.5 w-2.5 rounded-full ${indicatorClass}`} />
            {statusLabel}
          </span>
          <button
            type="button"
            className={`rounded-full px-4 py-2 text-sm transition ${
              enabled ? "bg-alert text-white hover:bg-rose-700" : "bg-ink text-white hover:bg-clay"
            }`}
            disabled={!supported}
            onClick={toggleVoiceControl}
          >
            {enabled ? "Apagar voz" : "Encender voz"}
          </button>
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-[1.2fr_0.8fr]">
        <article className="rounded-[1.5rem] bg-sand p-4">
          <p className="text-xs uppercase tracking-[0.18em] text-moss">Texto detectado</p>
          <p className="mt-2 min-h-12 text-sm text-ink">{transcript || "Habla para lanzar navegacion o comandos del robot."}</p>
        </article>
        <article className="rounded-[1.5rem] bg-sand p-4">
          <p className="text-xs uppercase tracking-[0.18em] text-moss">Ultima accion</p>
          <p className="mt-2 text-sm text-ink">{lastAction ?? "Sin acciones ejecutadas."}</p>
          {errorMessage ? <p className="mt-2 text-sm text-alert">{errorMessage}</p> : null}
        </article>
      </div>
    </section>
  );
}
