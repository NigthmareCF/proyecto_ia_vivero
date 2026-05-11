import { Client } from "@stomp/stompjs";
import { useEffect } from "react";
import { getRobotStatus } from "../api/robotApi";
import { normalizeRobotStatus, useRobotStore } from "../store/robotStore";
import { resolveSockJsUrl } from "../utils/socket";

export function useRobotWebSocket() {
  const setStatus = useRobotStore((state) => state.setStatus);

  useEffect(() => {
    let client: Client | null = null;
    let cancelled = false;

    void getRobotStatus()
      .then((status) => setStatus({ ...normalizeRobotStatus(status), isConnected: true }))
      .catch(() => setStatus({ isConnected: false, connectionQuality: "OFFLINE" }));

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
            setStatus({ isConnected: true, connectionQuality: "GOOD" });
            client?.subscribe("/topic/robot/status", (message) =>
              setStatus({ ...normalizeRobotStatus(JSON.parse(message.body)), isConnected: true }),
            );
          },
          onDisconnect: () => setStatus({ isConnected: false, connectionQuality: "OFFLINE" }),
          onWebSocketClose: () => setStatus({ isConnected: false, connectionQuality: "OFFLINE" }),
          onStompError: () => setStatus({ isConnected: false, connectionQuality: "OFFLINE" }),
        });

        try {
          client.activate();
        } catch {
          setStatus({ isConnected: false, connectionQuality: "OFFLINE" });
        }
      })
      .catch(() => {
        setStatus({ isConnected: false, connectionQuality: "OFFLINE" });
      });

    return () => {
      cancelled = true;
      if (client) {
        void client.deactivate();
      }
    };
  }, [setStatus]);
}
