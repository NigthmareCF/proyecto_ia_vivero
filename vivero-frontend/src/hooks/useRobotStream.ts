import { useEffect } from "react";
import { useRobotStore } from "../store/robotStore";
import { resolveRobotStreamWsUrl } from "../utils/robotWsUrls";

type RobotStreamPayload = {
  camera?: string;
  frame?: string;
};

export function useRobotStream() {
  const setStatus = useRobotStore((state) => state.setStatus);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: number | null = null;
    let isUnmounted = false;

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
        scheduleReconnect();
        return;
      }

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(String(event.data)) as RobotStreamPayload;
          if (!payload.frame) {
            return;
          }
          setStatus({
            latestStreamFrameUrl: `data:image/jpeg;base64,${payload.frame}`,
            latestStreamCamera: payload.camera?.toUpperCase() ?? "FRONT",
          });
        } catch (error) {
          console.error("No se pudo parsear el frame del robot", error);
        }
      };

      socket.onerror = (event) => {
        console.error("WebSocket error en stream del robot", event);
      };

      socket.onclose = () => {
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
      socket?.close();
    };
  }, [setStatus]);
}
