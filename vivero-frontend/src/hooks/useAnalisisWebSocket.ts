import { Client } from "@stomp/stompjs";
import SockJS from "sockjs-client";
import { useEffect } from "react";
import { useNotificationStore } from "../store/notificationStore";
import { resolveRobotSockJsUrl } from "../utils/robotWsUrls";

export function useAnalisisWebSocket(onMessage: (payload: unknown) => void) {
  const pushToast = useNotificationStore((state) => state.pushToast);

  useEffect(() => {
    let client: Client | null = null;

    try {
      client = new Client({
        webSocketFactory: () => new SockJS(resolveRobotSockJsUrl()),
        reconnectDelay: 5000,
        onConnect: () => {
          client?.subscribe("/topic/analisis", (message) => {
            try {
              onMessage(JSON.parse(message.body));
            } catch (error) {
              console.error("No se pudo parsear /topic/analisis", error);
            }
          });

          client?.subscribe("/topic/alertas", (message) => {
            try {
              const payload = JSON.parse(message.body);
              pushToast({
                id: crypto.randomUUID(),
                title: `Alerta critica: ${payload?.estadoGeneral ?? "sin estado"}`,
                variant: "critical",
              });
              onMessage(payload);
            } catch (error) {
              console.error("No se pudo parsear /topic/alertas", error);
            }
          });
        },
        onStompError: (frame) => {
          console.error("STOMP error en analisis", frame.headers["message"] ?? frame.body);
        },
        onWebSocketError: (event) => {
          console.error("WebSocket error en analisis", event);
        },
      });

      client.activate();
    } catch (error) {
      console.error("No se pudo inicializar el WebSocket de analisis", error);
    }

    return () => {
      if (client) {
        void client.deactivate();
      }
    };
  }, [onMessage, pushToast]);
}
