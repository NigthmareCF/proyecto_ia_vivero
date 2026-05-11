import { Client } from "@stomp/stompjs";
import { useEffect } from "react";
import { useNotificationStore } from "../store/notificationStore";
import { resolveSockJsUrl } from "../utils/socket";

export function useAnalisisWebSocket(onMessage: (payload: unknown) => void) {
  const pushToast = useNotificationStore((state) => state.pushToast);

  useEffect(() => {
    let client: Client | null = null;
    let cancelled = false;

    void import("sockjs-client")
      .then((module) => {
        if (cancelled) {
          return;
        }

        const SockJS = module.default;
        client = new Client({
          webSocketFactory: () => new SockJS(resolveSockJsUrl(import.meta.env.VITE_WS_URL)),
          reconnectDelay: 5000,
          onConnect: () => {
            client?.subscribe("/topic/analisis", (message) => onMessage(JSON.parse(message.body)));
            client?.subscribe("/topic/alertas", (message) => {
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

        try {
          client.activate();
        } catch {
          // Silencia fallos de websocket para no romper la vista de análisis.
        }
      })
      .catch(() => {
        // Si SockJS no carga, la vista sigue funcionando sin eventos en tiempo real.
      });

    return () => {
      cancelled = true;
      if (client) {
        void client.deactivate();
      }
    };
  }, [onMessage, pushToast]);
}
