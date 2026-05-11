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
import { useVoiceCommandStore } from "../../store/voiceCommandStore";
import { parseVoiceCommand } from "../../utils/voiceCommands";

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

export function VoiceCommandDock() {
  const navigate = useNavigate();
  const location = useLocation();
  const pushToast = useNotificationStore((state) => state.pushToast);
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
  const [isExecuting, setIsExecuting] = useState(false);

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

    recognition.onstart = () => {
      setStatus("listening");
      setErrorMessage(null);
    };

    recognition.onend = () => {
      if (shouldRestartRef.current) {
        recognition.start();
        return;
      }
      setStatus("idle");
    };

    recognition.onerror = (event) => {
      setStatus("error");
      setErrorMessage(`Reconocimiento de voz: ${event.error}`);
    };

    recognition.onresult = async (event) => {
      const latest = event.results[event.results.length - 1];
      const spokenText = latest?.[0]?.transcript?.trim() ?? "";
      if (!spokenText) {
        return;
      }
      setTranscript(spokenText);
      if (!latest.isFinal || isExecuting) {
        return;
      }

      const parsedCommand = parseVoiceCommand(spokenText);
      if (!parsedCommand) {
        setLastAction("Comando no reconocido");
        pushToast({
          id: crypto.randomUUID(),
          title: `Voz no reconocida: ${spokenText}`,
          variant: "info",
        });
        return;
      }

      setIsExecuting(true);
      setStatus("processing");
      setLastAction(parsedCommand.summary);
      try {
        if (location.pathname !== parsedCommand.path) {
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
        }

        pushToast({
          id: crypto.randomUUID(),
          title: `Voz: ${parsedCommand.summary}`,
          variant: "info",
        });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Error ejecutando comando de voz";
        setStatus("error");
        setErrorMessage(message);
      } finally {
        setIsExecuting(false);
        setStatus(enabled ? "listening" : "idle");
      }
    };

    recognitionRef.current = recognition;
    return () => {
      shouldRestartRef.current = false;
      recognition.stop();
      recognitionRef.current = null;
    };
  }, [
    enabled,
    isExecuting,
    location.pathname,
    navigate,
    pushToast,
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

    shouldRestartRef.current = enabled;
    if (enabled) {
      recognition.start();
      return;
    }
    recognition.stop();
  }, [enabled, supported]);

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
        : status === "processing"
          ? "Procesando"
          : status === "error"
            ? "Error"
            : "En espera";

  const indicatorClass =
    status === "listening"
      ? "bg-emerald-500"
      : status === "processing"
        ? "bg-amber-400"
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
