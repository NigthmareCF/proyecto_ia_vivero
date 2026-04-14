import { Client } from "@stomp/stompjs";
import SockJS from "sockjs-client";
import { useEffect } from "react";
import { useNotificationStore } from "../store/notificationStore";

export function useAnalisisWebSocket(onMessage: (payload: unknown) => void) {
  const pushToast = useNotificationStore((state) => state.pushToast);

  useEffect(() => {
    const client = new Client({
      webSocketFactory: () => new SockJS((import.meta.env.VITE_WS_URL ?? "http://localhost:8080/api") + "/ws"),
      reconnectDelay: 5000,
      onConnect: () => {
        client.subscribe("/topic/analisis", (message) => onMessage(JSON.parse(message.body)));
        client.subscribe("/topic/alertas", (message) => {
          const payload = JSON.parse(message.body);
          pushToast({
            id: crypto.randomUUID(),
            title: `Alerta critica: ${payload.estadoGeneral ?? "sin estado"}`,
            variant: "critical",
          });
          onMessage(payload);
        });
      },
    });

    client.activate();
    return () => {
      void client.deactivate();
    };
  }, [onMessage, pushToast]);
}
