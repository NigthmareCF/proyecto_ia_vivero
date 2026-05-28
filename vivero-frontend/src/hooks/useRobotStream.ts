import { useEffect } from "react";
import { useRobotStore } from "../store/robotStore";
import { resolveRobotStreamWsUrl } from "../utils/robotWsUrls";

type RobotStreamPayload = {
  camera?: string;
  frame?: string;
};

function base64ToBlobUrl(base64: string) {
  const binary = window.atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  const blob = new Blob([bytes], { type: "image/jpeg" });
  return URL.createObjectURL(blob);
}

export function useRobotStream() {
  const setStatus = useRobotStore((state) => state.setStatus);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: number | null = null;
    let isUnmounted = false;
    let currentFrameUrl: string | null = null;

    const scheduleReconnect = () => {
      if (reconnectTimer !== null) {
        window.clearTimeout(reconnectTimer);
      }
      reconnectTimer = window.setTimeout(connect, 3000);
    };

    const connect = () => {
      try {
        socket = new WebSocket(resolveRobotStreamWsUrl());
      } catch (error) {
        console.error("No se pudo abrir el stream del robot", error);
        setStatus({ streamSocketConnected: false });
        scheduleReconnect();
        return;
      }

      socket.onopen = () => {
        setStatus({ streamSocketConnected: true });
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(String(event.data)) as RobotStreamPayload;
          if (!payload.frame) {
            return;
          }
          const nextFrameUrl = base64ToBlobUrl(payload.frame);
          if (currentFrameUrl) {
            URL.revokeObjectURL(currentFrameUrl);
          }
          currentFrameUrl = nextFrameUrl;
          setStatus({
            latestStreamFrameUrl: nextFrameUrl,
            latestStreamCamera: payload.camera?.toUpperCase() ?? "FRONT",
            latestStreamFrameAt: new Date().toLocaleTimeString(),
            streamSocketConnected: true,
          });
        } catch (error) {
          console.error("No se pudo parsear el frame del robot", error);
        }
      };

      socket.onerror = (event) => {
        console.error("WebSocket error en stream del robot", event);
        setStatus({ streamSocketConnected: false });
      };

      socket.onclose = () => {
        setStatus({ streamSocketConnected: false });
        if (!isUnmounted) {
          scheduleReconnect();
        }
      };
    };

    connect();

    return () => {
      isUnmounted = true;
      if (reconnectTimer !== null) {
        window.clearTimeout(reconnectTimer);
      }
      if (currentFrameUrl) {
        URL.revokeObjectURL(currentFrameUrl);
      }
      socket?.close();
    };
  }, [setStatus]);
}
